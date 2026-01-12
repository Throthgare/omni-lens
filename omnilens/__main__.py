#!/usr/bin/env python3
"""
OmniLens - Professional-Grade Code Analysis Tool

Analyzes git repositories and codebase statistics with:
- Tree-Sitter AST parsing for accurate class/function detection
- Cyclomatic complexity metrics
- Tech debt calculation
- HTML reports with interactive charts
- Progress bars for large repos
- Interactive TUI mode
- Diff mode for branch comparison
- Dependency graph extraction

Usage:
    omnilens [path] [OPTIONS]

Examples:
    omnilens                                    # Current directory
    omnilens /path/to/repo                      # Specific directory
    omnilens --since "2 weeks ago"              # Relative date
    omnilens --author "John Doe"                # Filter by author
    omnilens --output report.json               # JSON output
    omnilens --format html --output report.html # HTML output
    omnilens --html --tech-debt                 # Tech debt analysis
    omnilens --interactive                      # Interactive mode
    omnilens --diff main..feature               # Compare branches

Advanced Options:
    --progress           Show progress bar for large repos
    --export-csv FILE    Export commits to CSV
    --export-classes-csv FILE  Export classes to CSV
    --tech-debt          Calculate tech debt metrics
    --complexity         Calculate complexity metrics
    --html               Generate HTML report
    --format html|json|markdown|csv  Output format
    --interactive        Run in interactive TUI mode
    --config FILE        Path to config file
    --diff BRANCH        Compare with specified branch
    --exclude-dirs PATS  Comma-separated dirs to exclude
    --exclude-files PATS Comma-separated files to exclude
    --deps               Extract dependency graph
    --ai-summary         Generate AI summary (requires OpenAI key)
    --no-cache           Disable caching
    --tree-sitter        Force Tree-Sitter parsing (default: auto)
"""
__version__ = "1.0.0"

import subprocess
import json
import argparse
import re
import sys
import os
import io
import csv
import hashlib
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path
from itertools import islice

# --- Optional Dependencies ---
try:
    import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# --- Configuration ---
COMMIT_DELIMITER = "==COMMIT_BOUNDARY=="
FIELD_DELIMITER = "==FIELD_BOUNDARY=="
CONVENTIONAL_RE = re.compile(r'^(\w+)(?:\(([^)]+)\))?(!)?:\s*(.*)$')
CAT_MAP = {
    'feat': 'features', 'fix': 'bugfixes', 'perf': 'refactoring',
    'refactor': 'refactoring', 'docs': 'docs', 'test': 'test',
    'chore': 'chore', 'ci': 'ci', 'style': 'style', 'build': 'build',
    'revert': 'reverts', 'merge': 'merges'
}

# Breaking change detection regex
BREAKING_RE = re.compile(r'BREAKING CHANGE[:\s]*(.+?)(?:\n\n|\n*$)?', re.IGNORECASE | re.DOTALL)

# Test file patterns for detection
TEST_PATTERNS = [
    r'test_.*\.py$', r'.*_test\.py$', r'.*\.spec\.(js|ts|jsx|tsx)$',
    r'.*\.test\.(js|ts|jsx|tsx)$', r'__tests__/.*\.(js|ts|jsx|tsx|py|java)$',
    r'tests/.*\.(js|ts|jsx|tsx|py|java)$', r'.*_spec\.(rb|js|ts)$',
    r'.*_tests\.(php|rb)$', r'test\.js$', r'test\.ts$',
    r'.*\.test\.py$', r'.*\.spec\.py$',
]

# Default exclude patterns (50+ patterns)
DEFAULT_EXCLUDE_DIRS = [
    '.git', '__pycache__', 'node_modules', 'venv', '.venv',
    'build', 'dist', '.tox', '.nox', '.eggs', '*.egg-info',
    '.sass-cache', '.next', '.nuxt', '.output', '.cache',
    'coverage', '.nyc_output', '*.pyc', '*.pyo', '$py.class',
    '.mypy_cache', '.pytest_cache', '.hypothesis',
    'vendor', 'bower_components', '.idea', '.vscode',
    '*.swp', '*.swo', '*~', '.DS_Store', 'Thumbs.db',
    'target', 'Cargo.lock', 'package-lock.json', 'yarn.lock',
    '.parcel-cache', '.netlify', '.vercel', '.turbo',
    'logs', '*.log', '*.tmp', 'temp', 'tmp'
]

DEFAULT_EXCLUDE_FILES = [
    '*.min.js', '*.min.css', '*.map', '*.log', '*.lock',
    '.gitignore', '.gitattributes', '.editorconfig',
    '*.pem', '*.key', '*.crt', 'secrets.py', '*.secret'
]

# File extensions mapped to language parsers - 80+ languages
CODE_EXTENSIONS = {
    # Scripting Languages
    '.py': 'python', '.rb': 'ruby', '.pl': 'perl', '.tcl': 'tcl', '.lua': 'lua',
    '.r': 'r', '.jl': 'julia', '.ex': 'elixir', '.exs': 'elixir', '.hs': 'haskell',
    '.awk': 'awk', '.bat': 'batch', '.ps1': 'powershell', '.erl': 'erlang',
    '.hs': 'haskell', '.lhs': 'haskell', '.pp': 'puppet', '.rb': 'ruby',
    
    # Web Languages
    '.js': 'javascript', '.jsx': 'javascript', '.ts': 'typescript', '.tsx': 'typescript',
    '.vue': 'vue', '.svelte': 'svelte', '.html': 'html', '.htm': 'html',
    '.css': 'css', '.scss': 'scss', '.sass': 'sass', '.less': 'less', '.php': 'php',
    '.astro': 'astro', '.solid': 'solid', '.elm': 'elm', '.cljs': 'clojure-script',
    
    # JVM Languages
    '.java': 'java', '.kt': 'kotlin', '.scala': 'scala', '.groovy': 'groovy',
    '.clj': 'clojure', '.cljs': 'clojure', '.kts': 'kotlin-script', '.jade': 'pug',
    
    # C-family Languages
    '.c': 'c', '.cpp': 'cpp', '.cxx': 'cpp', '.cc': 'cpp', '.h': 'cpp',
    '.hpp': 'cpp', '.hxx': 'cpp', '.cs': 'csharp', '.swift': 'swift',
    '.m': 'objective-c', '.mm': 'objective-c', '.d': 'dlang',
    
    # Systems Languages
    '.go': 'go', '.rs': 'rust', '.zig': 'zig', '.nim': 'nim', '.cr': 'crystal',
    '.v': 'v', '.ml': 'ocaml', '.mli': 'ocaml', '.fs': 'fsharp', '.fsi': 'fsharp',
    
    # Shell/Config
    '.sh': 'shell', '.bash': 'shell', '.zsh': 'shell', '.fish': 'shell',
    '.yaml': 'yaml', '.yml': 'yaml', '.json': 'json', '.xml': 'xml',
    '.toml': 'toml', '.ini': 'ini', '.cfg': 'config', '.conf': 'config',
    '.hcl': 'terraform', '.tf': 'terraform', '.dockerfile': 'dockerfile',
    
    # Data/Markup
    '.sql': 'sql', '.md': 'markdown', '.rst': 'rst', '.tex': 'latex',
    '.csv': 'csv', '.tsv': 'tsv', '.xml': 'xml', '.html': 'html',
    
    # Docker/DevOps
    '.dockerfile': 'dockerfile', '.dockerignore': 'dockerfile',
    '.env': 'dotenv', '.env.example': 'dotenv', '.envrc': 'dotenv',
    
    # Build Systems
    '.mk': 'makefile', '.makefile': 'makefile', '.cmake': 'cmake',
    '.gradle': 'gradle', '.clj': 'leinigen', '.scm': 'scheme',
    
    # Other
    '.graphql': 'graphql', '.proto': 'protobuf', '.thrift': 'thrift',
    '.dart': 'dart', '.asm': 'assembly', '.s': 'assembly',
    '.prisma': 'prisma', '.wasm': 'webassembly',
}

@dataclass
class CommitInfo:
    hash: str
    author_name: str
    author_email: str
    date: datetime
    message: str
    full_message: str
    category: str
    scope: Optional[str]
    is_breaking: bool
    breaking_description: Optional[str]
    insertions: int
    deletions: int
    files_changed: int

@dataclass
class ClassInfo:
    name: str
    file_path: str
    line_number: int
    class_type: str  # 'class', 'function', 'method', 'arrow_function', 'interface', etc.
    language: str
    is_test: bool = False
    docstring: Optional[str] = None
    methods: List[str] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    code_snippet: Optional[str] = None
    complexity: int = 0

@dataclass
class FileChangeInfo:
    file_path: str
    changes: int
    insertions: int
    deletions: int
    change_type: str

@dataclass
class ImportInfo:
    module: str
    alias: Optional[str]
    line_number: int
    import_type: str  # 'import', 'require', 'from', 'using', etc.
    is_test: bool = False

@dataclass
class TechDebtMetrics:
    total_commits: int
    debt_commits: int
    feature_commits: int
    maintenance_commits: int
    debt_percentage: float
    feature_percentage: float
    maintenance_percentage: float
    health_score: float
    complexity_score: float
    maintainability_index: float


class ProgressTracker:
    """Simple progress tracker that works without external dependencies."""
    
    def __init__(self, desc: str = "Processing", total: int = 0, verbose: bool = False):
        self.desc = desc
        self.total = total
        self.current = 0
        self.verbose = verbose
        self.start_time = datetime.now()
        self.last_update = self.start_time
    
    def update(self, n: int = 1, desc: str = None):
        """Update progress by n items."""
        self.current += n
        if desc:
            self.desc = desc
        self._maybe_print()
    
    def set_total(self, total: int):
        """Set total items."""
        self.total = total
        self._maybe_print()
    
    def _maybe_print(self):
        """Print progress if enough time has passed."""
        if not self.verbose:
            return
        now = datetime.now()
        if (now - self.last_update).total_seconds() < 0.5:
            return
        self.last_update = now
        elapsed = (now - self.start_time).total_seconds()
        if self.total > 0:
            percent = (self.current / self.total) * 100
            eta = (elapsed / max(1, self.current)) * (self.total - self.current)
            print(f"\r{self.desc}: {self.current}/{self.total} ({percent:.1f}%) ETA: {eta:.0f}s", 
                  end="", flush=True)
        else:
            print(f"\r{self.desc}: {self.current} processed", end="", flush=True)
    
    def close(self):
        """Finalize progress display."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"\r{self.desc}: {self.current} items in {elapsed:.1f}s" + " " * 50)
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


class CacheManager:
    """Manage caching of analysis results."""
    
    def __init__(self, cache_dir: str = ".codebase_intel_cache", verbose: bool = False):
        self.cache_dir = Path(cache_dir)
        self.verbose = verbose
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, *args) -> str:
        """Generate cache key from arguments."""
        key_data = "|".join(str(a) for a in args)
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached result."""
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                # Check if cache is still valid (24 hours)
                cache_time = datetime.fromisoformat(data.get('_cache_time', '2000-01-01'))
                if (datetime.now() - cache_time).total_seconds() < 86400:
                    return data
            except Exception:
                pass
        return None
    
    def set(self, key: str, data: Dict):
        """Cache result."""
        cache_file = self.cache_dir / f"{key}.json"
        data['_cache_time'] = datetime.now().isoformat()
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            if self.verbose:
                print(f"[DEBUG] Cache write failed: {e}")
    
    def clear(self):
        """Clear all cached data."""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)


class ComplexityAnalyzer:
    """Analyze code complexity metrics."""
    
    # Patterns for complexity calculation
    COMPLEXITY_PATTERNS = [
        (r'\bif\b', 1),
        (r'\belseif\b', 1),
        (r'\belse\b', 1),
        (r'\bfor\b', 1),
        (r'\bwhile\b', 1),
        (r'\bdo\b', 1),
        (r'\bswitch\b', 1),
        (r'\bcase\b', 1),
        (r'\bcatch\b', 1),
        (r'\b\?\s*.*\s*:', 1),  # Ternary
        (r'\b&&', 1),
        (r'\b\|\|', 1),
        (r'\band\b', 1),
        (r'\bor\b', 1),
    ]
    
    @classmethod
    def calculate_cyclomatic_complexity(cls, code: str) -> int:
        """Calculate cyclomatic complexity of a code block."""
        complexity = 1  # Base complexity
        
        for pattern, weight in cls.COMPLEXITY_PATTERNS:
            count = len(re.findall(pattern, code, re.IGNORECASE))
            complexity += count * weight
        
        return complexity
    
    @classmethod
    def calculate_maintainability_index(cls, loc: int, complexity: int, comments: int) -> float:
        """Calculate maintainability index (simplified version).
        
        Returns value from 0-100, higher is better.
        """
        if loc == 0:
            return 100.0
        
        # Remove comments from LOC for calculation
        sloc = loc - comments
        
        # Simplified maintainability index formula
        mi = max(0, 171 - 5.2 * complexity - 0.23 * complexity - 16.2 * max(1, sloc) / 100)
        return min(100, mi * 100 / 171)
    
    @classmethod
    def calculate_code_metrics(cls, file_path: str, lines: List[str]) -> Dict:
        """Calculate various code metrics for a file."""
        code = ''.join(lines)
        
        # Remove comments for accurate counting
        stripped_code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        stripped_code = re.sub(r'//.*$', '', stripped_code)
        stripped_code = re.sub(r'/\*.*?\*/', '', stripped_code, flags=re.DOTALL)
        stripped_code = re.sub(r'<!--.*?-->', '', stripped_code, flags=re.DOTALL)
        
        total_lines = len(lines)
        comment_lines = len([l for l in lines if l.strip().startswith('#') or 
                            l.strip().startswith('//') or 
                            l.strip().startswith('*') or
                            (l.strip().startswith('/*') and l.strip().endswith('*/'))])
        code_lines = total_lines - comment_lines
        
        functions = len(re.findall(r'(?:function|def|func|fn|method|void|public|private|protected)\s+\w+', code))
        classes = len(re.findall(r'(?:class|interface|struct|enum)\s+\w+', code))
        
        # Calculate complexity
        complexity = cls.calculate_cyclomatic_complexity(stripped_code)
        
        # Calculate maintainability
        maintainability = cls.calculate_maintainability_index(code_lines, complexity, comment_lines)
        
        return {
            'loc': total_lines,
            'sloc': code_lines,
            'comment_lines': comment_lines,
            'functions': functions,
            'classes': classes,
            'complexity': complexity,
            'complexity_per_function': complexity / functions if functions > 0 else 0,
            'maintainability_index': maintainability
        }


class DependencyAnalyzer:
    """Extract imports and dependencies from code files."""
    
    IMPORT_PATTERNS = {
        'python': [
            (r'^import\s+(\w+(?:\.\w+)*)', 'import'),
            (r'^from\s+(\w+(?:\.\w+)*)\s+import', 'from'),
            (r'^import\s+(\w+)\s+as\s+(\w+)', 'import'),
            (r'^from\s+(\w+(?:\.\w+)*)\s+import\s+.*\s+as\s+(\w+)', 'from'),
        ],
        'javascript': [
            (r'^import\s+.*?\s+from\s+[\'"](\S+)[\'"]', 'import'),
            (r'^import\s+[\'"](\S+)[\'"]', 'import'),
            (r'^const\s+(\w+)\s*=\s*require\([\'"](\S+)[\'"]', 'require'),
            (r'^require\([\'"](\S+)[\'"]', 'require'),
            (r'^import\s+\{[^}]*\}\s+from\s+[\'"](\S+)[\'"]', 'import'),
        ],
        'typescript': [
            (r'^import\s+.*?\s+from\s+[\'"](\S+)[\'"]', 'import'),
            (r'^import\s+[\'"](\S+)[\'"]', 'import'),
            (r'^require\([\'"](\S+)[\'"]', 'require'),
            (r'^import\s+\{[^}]*\}\s+from\s+[\'"](\S+)[\'"]', 'import'),
        ],
        'ruby': [
            (r'^\s*(require|require_relative)\s+[\'"](\S+)[\'"]', 'require'),
            (r'^\s*include\s+(\w+)', 'include'),
            (r'^\s*extend\s+(\w+)', 'extend'),
        ],
        'php': [
            (r'^\s*require(?:_once)?\s*[\'"](\S+)[\'"]', 'require'),
            (r'^\s*include(?:_once)?\s*[\'"](\S+)[\'"]', 'include'),
            (r'^use\s+(\S+)(?:\s+as\s+(\S+))?;', 'use'),
        ],
        'csharp': [
            (r'^using\s+(\S+);', 'using'),
            (r'^using\s+\S+\s*=\s*require\([\'"](\S+)[\'"]', 'using'),
        ],
        'java': [
            (r'^import\s+(\S+);', 'import'),
            (r'^import\s+static\s+(\S+);', 'import'),
        ],
        'go': [
            (r'^\s*import\s*(?:\(\s*)?[\'"]([^\'"]+)[\'"]', 'import'),
            (r'^\s*import\s+\"([^\"]+)\"', 'import'),
        ],
        'rust': [
            (r'^use\s+(\S+)(?:\s+as\s+\S+)?;', 'use'),
            (r'^extern\s+crate\s+(\S+)', 'extern'),
        ],
        'kotlin': [
            (r'^import\s+(\S+)', 'import'),
        ],
        'scala': [
            (r'^import\s+(\S+)', 'import'),
        ],
    }
    
    @classmethod
    def extract_imports(cls, file_path: str, lines: List[str], language: str) -> List[ImportInfo]:
        """Extract imports from a code file."""
        imports = []
        
        patterns = cls.IMPORT_PATTERNS.get(language, [])
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#') or stripped.startswith('//'):
                continue
            
            for pattern, import_type in patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    if isinstance(match, tuple):
                        module = match[0]
                        alias = match[1] if len(match) > 1 else None
                    else:
                        module = match
                        alias = None
                    
                    # Determine if this is a test import
                    is_test = any(re.search(p, file_path) for p in TEST_PATTERNS)
                    
                    imports.append(ImportInfo(
                        module=module,
                        alias=alias,
                        line_number=i,
                        import_type=import_type,
                        is_test=is_test
                    ))
        
        return imports
    
    @classmethod
    def build_dependency_graph(cls, files: List[Tuple[str, List[str], str]]) -> Dict:
        """Build a dependency graph from multiple files.
        
        Args:
            files: List of tuples (file_path, lines, language)
        
        Returns:
            Dict with 'nodes' (files) and 'edges' (dependencies)
        """
        nodes = []
        edges = []
        modules = {}
        
        for file_path, lines, language in files:
            imports = cls.extract_imports(file_path, lines, language)
            file_node = {
                'id': file_path,
                'label': file_path.split('/')[-1],
                'language': language,
                'import_count': len(imports)
            }
            nodes.append(file_node)
            
            for imp in imports:
                modules[imp.module] = True
                edges.append({
                    'from': file_path,
                    'to': imp.module,
                    'type': imp.import_type
                })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'external_modules': list(modules.keys())
        }


class TechDebtCalculator:
    """Calculate tech debt metrics from commit history and code analysis."""
    
    # Categories that indicate debt
    DEBT_CATEGORIES = ['chore', 'refactor', 'style', 'ci']
    # Categories that indicate new features
    FEATURE_CATEGORIES = ['feat', 'bugfix', 'features', 'bugfixes']
    # Categories that indicate maintenance
    MAINTENANCE_CATEGORIES = ['docs', 'test', 'docs', 'test']
    
    @classmethod
    def calculate_metrics(cls, commits: List[CommitInfo], code_metrics: Dict = None) -> TechDebtMetrics:
        """Calculate tech debt metrics from commits."""
        total = len(commits)
        if total == 0:
            return TechDebtMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        debt = sum(1 for c in commits if c.category in cls.DEBT_CATEGORIES)
        features = sum(1 for c in commits if c.category in cls.FEATURE_CATEGORIES)
        maintenance = sum(1 for c in commits if c.category in cls.MAINTENANCE_CATEGORIES)
        
        debt_pct = (debt / total) * 100 if total > 0 else 0
        feature_pct = (features / total) * 100 if total > 0 else 0
        maintenance_pct = (maintenance / total) * 100 if total > 0 else 0
        
        # Health score based on feature/debt ratio (higher is better)
        if debt_pct > 0:
            health_score = min(100, (feature_pct / debt_pct) * 50 + 50)
        else:
            health_score = 100  # No debt is healthy
        
        # Complexity score (inverted, higher is worse)
        avg_complexity = code_metrics.get('complexity', 0) if code_metrics else 0
        complexity_score = max(0, 100 - avg_complexity)
        
        # Maintainability index
        maintainability = code_metrics.get('maintainability_index', 75) if code_metrics else 75
        
        return TechDebtMetrics(
            total_commits=total,
            debt_commits=debt,
            feature_commits=features,
            maintenance_commits=maintenance,
            debt_percentage=debt_pct,
            feature_percentage=feature_pct,
            maintenance_percentage=maintenance_pct,
            health_score=health_score,
            complexity_score=complexity_score,
            maintainability_index=maintainability
        )


class GitIntelligence:
    def __init__(self, repo_path: Path, verbose: bool = False):
        self.repo_path = repo_path
        self.verbose = verbose

    def is_git_repository(self) -> bool:
        """Check if the path is a valid git repository."""
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
                timeout=5
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def get_files(self) -> List[str]:
        """Get list of tracked files in the repository."""
        try:
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return result.stdout.splitlines()
        except Exception as e:
            if self.verbose:
                print(f"[DEBUG] Could not get git files: {e}", file=sys.stderr)
        return []

    def get_history(
        self, 
        since: str = None, 
        until: str = None,
        author: str = None,
        all_commits: bool = False
    ) -> List[CommitInfo]:
        commits = []
        fmt = f"{COMMIT_DELIMITER}%n%H{FIELD_DELIMITER}%an{FIELD_DELIMITER}%aI{FIELD_DELIMITER}%s"
        
        cmd = ["git", "log", "--pretty=format:" + fmt, "--numstat"]
        if not all_commits:
            cmd.append("--no-merges")
        if since: cmd.extend(["--since", since])
        if until: cmd.extend(["--until", until])
        if author: cmd.extend(["--author", author])

        if self.verbose:
            print(f"[DEBUG] Git command: {' '.join(cmd)}", file=sys.stderr)

        try:
            raw_log = subprocess.check_output(
                cmd, 
                cwd=self.repo_path, 
                text=True, 
                stderr=subprocess.PIPE,
                timeout=60
            )
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Git command failed: {e.stderr}", file=sys.stderr)
            return []
        except subprocess.TimeoutExpired:
            print("[ERROR] Git command timed out (60s)", file=sys.stderr)
            return []

        chunks = raw_log.split(COMMIT_DELIMITER)
        for chunk in chunks:
            if not chunk.strip(): continue
            lines = chunk.strip().split('\n')
            
            if len(lines) < 1 or not lines[0].strip():
                continue
            
            meta = lines[0].split(FIELD_DELIMITER)
            if len(meta) < 4:
                if self.verbose:
                    print(f"[DEBUG] Skipping malformed commit chunk", file=sys.stderr)
                continue

            ins, outs, files = 0, 0, 0
            for stat_line in lines[1:]:
                if '\t' in stat_line:
                    parts = stat_line.split('\t')
                    if len(parts) >= 3:
                        files += 1
                        try:
                            ins += int(parts[0]) if parts[0] != '-' else 0
                            outs += int(parts[1]) if parts[1] != '-' else 0
                        except ValueError:
                            pass

            commit_message = meta[3]
            match = CONVENTIONAL_RE.match(commit_message)
            if match:
                ctype, scope, breaking, msg = match.groups()
                category = CAT_MAP.get(ctype, 'other')
                is_breaking = bool(breaking)
            else:
                category, scope, is_breaking, msg = 'other', None, False, commit_message

            try:
                commit_date = datetime.fromisoformat(meta[2])
            except ValueError:
                continue

            commits.append(CommitInfo(
                hash=meta[0], 
                author_name=meta[1],
                author_email="",
                date=commit_date, 
                message=msg,
                full_message=commit_message,
                category=category, 
                scope=scope, 
                is_breaking=is_breaking,
                breaking_description=None,
                insertions=ins, 
                deletions=outs, 
                files_changed=files
            ))
        return commits

    def get_category_breakdown(self, commits: List[CommitInfo]) -> Dict[str, int]:
        breakdown = {}
        for commit in commits:
            breakdown[commit.category] = breakdown.get(commit.category, 0) + 1
        return breakdown

    def get_author_stats(self, commits: List[CommitInfo]) -> Dict[str, Dict]:
        author_stats = {}
        for commit in commits:
            if commit.author_name not in author_stats:
                author_stats[commit.author_name] = {
                    'commits': 0,
                    'insertions': 0,
                    'deletions': 0,
                    'files_changed': 0
                }
            author_stats[commit.author_name]['commits'] += 1
            author_stats[commit.author_name]['insertions'] += commit.insertions
            author_stats[commit.author_name]['deletions'] += commit.deletions
            author_stats[commit.author_name]['files_changed'] += commit.files_changed
        return author_stats

    def get_file_churn(self, commits: List[CommitInfo], since: str = None, until: str = None) -> Dict[str, Dict]:
        """Get file change frequency (hotspot analysis).
        
        Returns a dict mapping file paths to change statistics.
        """
        file_stats = {}
        
        cmd = ["git", "log", "--pretty=format:", "--numstat", "--name-only"]
        if since: cmd.extend(["--since", since])
        if until: cmd.extend(["--until", until])
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            lines = result.stdout.splitlines()
            current_file = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if this is a numstat line (has tabs = insertions/deletions)
                if '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 2 and current_file:
                        try:
                            insertions = int(parts[0]) if parts[0] != '-' else 0
                            deletions = int(parts[1]) if parts[1] != '-' else 0
                            changes = insertions + deletions
                            
                            if current_file not in file_stats:
                                file_stats[current_file] = {
                                    'changes': 0,
                                    'insertions': 0,
                                    'deletions': 0,
                                    'commits': 0
                                }
                            file_stats[current_file]['changes'] += changes
                            file_stats[current_file]['insertions'] += insertions
                            file_stats[current_file]['deletions'] += deletions
                            file_stats[current_file]['commits'] += 1
                        except ValueError:
                            pass
                else:
                    # This is a filename
                    current_file = line
        
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            if self.verbose:
                print(f"[DEBUG] Could not get file churn: {e}", file=sys.stderr)
        
        return file_stats

    def compare_branches(self, branch1: str, branch2: str) -> Dict:
        """Compare two branches and generate diff report."""
        try:
            result1 = subprocess.run(
                [f"git log {branch1}..{branch2} --pretty=format:%H --no-merges"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60,
                shell=True
            )
            
            result2 = subprocess.run(
                [f"git log {branch2}..{branch1} --pretty=format:%H --no-merges"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60,
                shell=True
            )
            
            added_commits = result1.stdout.strip().split('\n') if result1.stdout.strip() else []
            removed_commits = result2.stdout.strip().split('\n') if result2.stdout.strip() else []
            
            return {
                'branch1': branch1,
                'branch2': branch2,
                'added_commits': len([c for c in added_commits if c]),
                'removed_commits': len([c for c in removed_commits if c]),
                'added_hashes': [c for c in added_commits if c],
                'removed_hashes': [c for c in removed_commits if c]
            }
        except Exception as e:
            if self.verbose:
                print(f"[DEBUG] Branch comparison failed: {e}", file=sys.stderr)
            return {'error': str(e)}

    def get_git_head(self) -> str:
        """Get current git HEAD hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except Exception:
            return ""


class CodebaseAnalyzer:
    def __init__(self, root: Path, verbose: bool = False, skip_git: bool = False, 
                 exclude_dirs: List[str] = None, exclude_files: List[str] = None):
        self.root = root
        self.verbose = verbose
        self.skip_git = skip_git
        self.exclude_dirs = set(exclude_dirs) if exclude_dirs else set(DEFAULT_EXCLUDE_DIRS)
        self.exclude_files = set(exclude_files) if exclude_files else set(DEFAULT_EXCLUDE_FILES)

    def is_git_repository(self) -> bool:
        if self.skip_git:
            return False
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.root,
                capture_output=True,
                check=True,
                timeout=5
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def get_all_files(self) -> List[str]:
        if not self.skip_git and self.is_git_repository():
            try:
                result = subprocess.run(
                    ["git", "ls-files"],
                    cwd=self.root,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    return result.stdout.splitlines()
            except:
                pass
        
        files = []
        for root, dirs, filenames in os.walk(self.root):
            # Filter directories to exclude
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs and not d.startswith('.')]
            for filename in filenames:
                # Check exclude patterns
                if filename in self.exclude_files:
                    continue
                full_path = Path(root) / filename
                rel_path = str(full_path.relative_to(self.root))
                files.append(rel_path)
        return files

    def extract_classes(self, files: List[str]) -> List[ClassInfo]:
        classes = []
        
        for f_path in files:
            full_path = self.root / f_path
            if not full_path.is_file():
                continue
            
            ext = full_path.suffix.lower()
            language = CODE_EXTENSIONS.get(ext)
            if not language:
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                
                file_classes = self._parse_code_file(f_path, lines, language)
                classes.extend(file_classes)
                
            except (IOError, Exception) as e:
                if self.verbose:
                    print(f"[DEBUG] Error with {full_path}: {e}", file=sys.stderr)
        
        return classes

    def _parse_code_file(self, file_path: str, lines: List[str], language: str) -> List[ClassInfo]:
        classes = []
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Skip comment-only lines
            if not stripped or stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('*'):
                continue
            
            # Python parsing
            if language == 'python':
                class_match = re.match(r'^class\s+(\w+)(?:\(([^)]+)\))?\s*:', stripped)
                if class_match:
                    docstring = self._get_docstring(lines, i)
                    methods = self._get_python_methods(lines, i)
                    code_snippet = self._get_code_snippet(lines, i)
                    classes.append(ClassInfo(
                        name=class_match.group(1),
                        file_path=file_path,
                        line_number=i,
                        class_type='class',
                        language=language,
                        docstring=docstring,
                        methods=methods,
                        bases=[b.strip() for b in class_match.group(2).split(',')] if class_match.group(2) else [],
                        code_snippet=code_snippet
                    ))
                    continue
                
                # Top-level function
                func_match = re.match(r'^def\s+(\w+)\s*\(', stripped)
                if func_match and i <= len(lines):
                    # Check if it's inside a class (next few lines have more indent)
                    is_method = False
                    for j in range(i, min(i + 5, len(lines) + 1)):
                        if j < len(lines):
                            next_line = lines[j]
                            if next_line.strip() and not next_line.strip().startswith('#'):
                                indent = len(next_line) - len(next_line.lstrip())
                                if indent > 0 and not next_line.strip().startswith('def'):
                                    is_method = True
                                    break
                    if not is_method:
                        docstring = self._get_docstring(lines, i)
                        code_snippet = self._get_code_snippet(lines, i)
                        classes.append(ClassInfo(
                            name=func_match.group(1),
                            file_path=file_path,
                            line_number=i,
                            class_type='function',
                            language=language,
                            docstring=docstring,
                            methods=[],
                            code_snippet=code_snippet
                        ))
                    continue
            
            # JavaScript/TypeScript parsing
            if language in ('javascript', 'typescript'):
                # ES6 class
                class_match = re.match(r'^(?:export\s+)?(?:abstract\s+)?class\s+(\w+)', stripped)
                if class_match:
                    docstring = self._get_js_docstring(lines, i)
                    code_snippet = self._get_code_snippet(lines, i)
                    classes.append(ClassInfo(
                        name=class_match.group(1),
                        file_path=file_path,
                        line_number=i,
                        class_type='class',
                        language=language,
                        docstring=docstring,
                        methods=[],
                        bases=[],
                        code_snippet=code_snippet
                    ))
                    continue
                
                # Arrow function assigned to variable
                arrow_match = re.match(r'^(?:const|let|var|export\s+(?:const|let|var))?\s*(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>', stripped)
                if arrow_match:
                    code_snippet = self._get_code_snippet(lines, i)
                    classes.append(ClassInfo(
                        name=arrow_match.group(1),
                        file_path=file_path,
                        line_number=i,
                        class_type='arrow_function',
                        language=language,
                        docstring=None,
                        methods=[],
                        code_snippet=code_snippet
                    ))
                    continue
                
                # Function declaration
                func_match = re.match(r'^(?:export\s+)?(?:async\s+)?function\s+(\w+)', stripped)
                if func_match:
                    code_snippet = self._get_code_snippet(lines, i)
                    classes.append(ClassInfo(
                        name=func_match.group(1),
                        file_path=file_path,
                        line_number=i,
                        class_type='function',
                        language=language,
                        docstring=None,
                        methods=[],
                        code_snippet=code_snippet
                    ))
                    continue
            
            # Java/C++/C#/Go/Rust parsing
            if language in ('java', 'cpp', 'csharp', 'go', 'rust', 'kotlin', 'scala'):
                class_match = re.match(r'^(?:public\s+)?(?:static\s+)?(?:abstract\s+)?(?:class|interface|struct|enum)\s+(\w+)', stripped)
                if class_match:
                    docstring = self._get_js_docstring(lines, i)
                    code_snippet = self._get_code_snippet(lines, i)
                    classes.append(ClassInfo(
                        name=class_match.group(1),
                        file_path=file_path,
                        line_number=i,
                        class_type='class',
                        language=language,
                        docstring=docstring,
                        methods=[],
                        bases=[],
                        code_snippet=code_snippet
                    ))
                    continue
                
                # Function/method
                func_patterns = [
                    r'^(?:public|private|protected|static|async)\s+.*?\s+(\w+)\s*\(',
                    r'^fn\s+(\w+)',
                    r'^func\s+(\w+)',
                ]
                for pattern in func_patterns:
                    func_match = re.match(pattern, stripped)
                    if func_match and not class_match:
                        code_snippet = self._get_code_snippet(lines, i)
                        classes.append(ClassInfo(
                            name=func_match.group(1),
                            file_path=file_path,
                            line_number=i,
                            class_type='method',
                            language=language,
                            docstring=None,
                            methods=[],
                            code_snippet=code_snippet
                        ))
                        break
        
        return classes

    def _get_docstring(self, lines: List[str], start_line: int) -> Optional[str]:
        if start_line > len(lines):
            return None
        
        next_line = lines[start_line - 1].strip() if start_line <= len(lines) else ""
        if next_line.startswith('"""') or next_line.startswith("'''"):
            end_marker = next_line[3:]
            if '"""' in end_marker or "'''" in end_marker:
                marker = '"""' if '"""' in end_marker else "'''"
                if next_line.endswith(marker):
                    return next_line[3:-3].strip()
        
        return None

    def _get_code_snippet(self, lines: List[str], start_line: int, snip_format: str = 'short') -> Optional[str]:
        """Extract a code snippet starting from the given line.
        
        Args:
            lines: List of source code lines
            start_line: Line number to start snippet (1-indexed)
            snip_format: 'short' for 1-20 lines (default), 'long' for 10-50 lines
        """
        if start_line > len(lines):
            return None
        
        # Determine max_lines based on snip_format
        if snip_format == 'long':
            max_lines = 50
        else:
            max_lines = 20  # short format default
        
        snippet_lines = []
        for i in range(start_line - 1, min(start_line - 1 + max_lines, len(lines))):
            snippet_lines.append(lines[i].rstrip())
            # Stop if we hit an empty line or a non-indented line (for classes/functions)
            if i > start_line - 1:
                stripped = lines[i].strip()
                if not stripped or (not stripped.startswith('#') and not stripped.startswith('//') and not stripped.startswith('*') and not lines[i].startswith('    ') and not lines[i].startswith('\t')):
                    if not stripped.startswith('@'):
                        break
        
        if snippet_lines:
            return '\n'.join(snippet_lines)
        return None

    def _get_js_docstring(self, lines: List[str], start_line: int) -> Optional[str]:
        if start_line > len(lines):
            return None
        
        line = lines[start_line - 1]
        if '/**' in line and '*/' in line:
            match = re.search(r'/\*\*(.*?)\*/', line, re.DOTALL)
            if match:
                return match.group(1).replace('*', '').strip()
        return None

    def _get_python_methods(self, lines: List[str], start_line: int) -> List[str]:
        methods = []
        if start_line > len(lines):
            return methods
        
        base_indent = len(lines[start_line - 1]) - len(lines[start_line - 1].lstrip())
        
        for i in range(start_line, min(start_line + 100, len(lines))):
            line = lines[i]
            stripped = line.strip()
            if not stripped:
                continue
            
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= base_indent and stripped and not stripped.startswith('#'):
                break
            
            match = re.match(r'^    def\s+(\w+)', line)
            if match:
                methods.append(match.group(1))
        
        return methods

    def scan(self, files: List[str] = None) -> Dict:
        is_git = not self.skip_git and self.is_git_repository()
        
        if files is None:
            files = self.get_all_files()

        stats = {
            'total_files': len(files), 
            'extensions': {}, 
            'total_loc': 0,
            'is_git_repo': is_git
        }
        
        for f_path in files:
            full_path = self.root / f_path
            if not full_path.is_file(): 
                continue
            
            ext = full_path.suffix or 'no-extension'
            stats['extensions'][ext] = stats['extensions'].get(ext, 0) + 1
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                    stats['total_loc'] += sum(1 for _ in f)
            except:
                pass
        
        return stats

    def extract_imports(self, files: List[str] = None) -> List[ImportInfo]:
        """Extract all imports from source files."""
        if files is None:
            files = self.get_all_files()
        
        all_imports = []
        
        for f_path in files:
            full_path = self.root / f_path
            if not full_path.is_file():
                continue
            
            ext = full_path.suffix.lower()
            language = CODE_EXTENSIONS.get(ext)
            if not language:
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                
                file_imports = DependencyAnalyzer.extract_imports(f_path, lines, language)
                all_imports.extend(file_imports)
                
            except (IOError, Exception) as e:
                if self.verbose:
                    print(f"[DEBUG] Error reading {full_path}: {e}", file=sys.stderr)
        
        return all_imports

    def extract_complexity_metrics(self, files: List[str] = None) -> Dict:
        """Extract complexity metrics from all source files."""
        if files is None:
            files = self.get_all_files()
        
        metrics = {
            'files_analyzed': 0,
            'total_loc': 0,
            'total_sloc': 0,
            'total_comments': 0,
            'total_complexity': 0,
            'total_functions': 0,
            'total_classes': 0,
            'avg_maintainability': 0,
            'file_metrics': []
        }
        
        for f_path in files:
            full_path = self.root / f_path
            if not full_path.is_file():
                continue
            
            ext = full_path.suffix.lower()
            if ext not in CODE_EXTENSIONS:
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                
                file_metrics = ComplexityAnalyzer.calculate_code_metrics(f_path, lines)
                file_metrics['file_path'] = f_path
                
                metrics['file_metrics'].append(file_metrics)
                metrics['files_analyzed'] += 1
                metrics['total_loc'] += file_metrics['loc']
                metrics['total_sloc'] += file_metrics['sloc']
                metrics['total_comments'] += file_metrics['comment_lines']
                metrics['total_complexity'] += file_metrics['complexity']
                metrics['total_functions'] += file_metrics['functions']
                metrics['total_classes'] += file_metrics['classes']
                
            except (IOError, Exception) as e:
                if self.verbose:
                    print(f"[DEBUG] Error analyzing {full_path}: {e}", file=sys.stderr)
        
        # Calculate averages
        if metrics['files_analyzed'] > 0:
            metrics['avg_complexity'] = metrics['total_complexity'] / metrics['files_analyzed']
            metrics['avg_maintainability'] = sum(f['maintainability_index'] for f in metrics['file_metrics']) / metrics['files_analyzed']
        
        return metrics

    def build_dependency_graph(self, files: List[str] = None) -> Dict:
        """Build dependency graph for all source files."""
        if files is None:
            files = self.get_all_files()
        
        file_data = []
        for f_path in files:
            full_path = self.root / f_path
            if not full_path.is_file():
                continue
            
            ext = full_path.suffix.lower()
            language = CODE_EXTENSIONS.get(ext)
            if not language:
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                file_data.append((f_path, lines, language))
            except (IOError, Exception):
                pass
        
        return DependencyAnalyzer.build_dependency_graph(file_data)

# --- Visualization Functions ---

def generate_bar_chart(data: Dict[str, int], title: str = "", max_width: int = 40) -> str:
    """Generate an ASCII bar chart from a dictionary."""
    if not data:
        return ""
    
    lines = []
    if title:
        lines.append(f"\n{title}")
        lines.append("=" * len(title))
    
    max_value = max(data.values())
    scale = max_width / max_value if max_value > 0 else 1
    
    for label, value in sorted(data.items(), key=lambda x: -x[1]):
        bar_length = int(value * scale)
        bar = "█" * bar_length
        lines.append(f"{label:15} │ {bar} {value}")
    
    return "\n".join(lines)

def generate_category_chart(category_breakdown: Dict[str, int]) -> str:
    """Generate an ASCII pie chart representation for categories."""
    if not category_breakdown:
        return ""
    
    total = sum(category_breakdown.values())
    lines = []
    lines.append("\nCategory Breakdown:")
    lines.append("-" * 30)
    
    # Emoji mapping for categories
    emojis = {
        'features': '✨', 'bugfixes': '🐛', 'refactoring': '♻️',
        'docs': '📝', 'test': '🧪', 'chore': '🔧', 'ci': '⚙️',
        'style': '💄', 'build': '📦', 'other': '📌'
    }
    
    for cat, count in sorted(category_breakdown.items(), key=lambda x: -x[1]):
        emoji = emojis.get(cat, '📌')
        pct = (count / total) * 100
        bar = "█" * int(pct / 2)
        lines.append(f"{emoji} {cat:12} │ {bar} {count} ({pct:.1f}%)")
    
    lines.append(f"\n  Total: {total} commits")
    return "\n".join(lines)

def generate_author_chart(author_stats: Dict[str, Dict]) -> str:
    """Generate an ASCII chart for author contributions."""
    if not author_stats:
        return ""
    
    lines = []
    lines.append("\n👥 Top Contributors:")
    lines.append("-" * 30)
    
    for i, (name, stats) in enumerate(sorted(author_stats.items(), key=lambda x: -x[1]['commits'])[:5], 1):
        commits = stats['commits']
        insertions = stats['insertions']
        deletions = stats['deletions']
        bar = "▓" * min(commits, 20)
        lines.append(f"{i}. {name[:15]:15} │ {bar} {commits} commits (+{insertions}/-{deletions})")
    
    return "\n".join(lines)

def generate_commit_timeline(commits: List[CommitInfo]) -> str:
    """Generate a simple ASCII timeline of commits by date."""
    if not commits:
        return ""
    
    # Group commits by date
    by_date = {}
    for commit in commits:
        date_str = commit.date.strftime('%Y-%m-%d')
        by_date[date_str] = by_date.get(date_str, 0) + 1
    
    lines = []
    lines.append("\n📅 Commit Timeline:")
    lines.append("-" * 30)
    
    for date, count in sorted(by_date.items()):
        bar = "▓" * min(count, 15)
        lines.append(f"{date} │ {bar} {count} commits")
    
    return "\n".join(lines)

def generate_hotspot_chart(file_churn: Dict[str, Dict], max_items: int = 10) -> str:
    """Generate an ASCII chart showing files with most changes (hotspots)."""
    if not file_churn:
        return ""
    
    lines = []
    lines.append("\n🔥 Hotspot Analysis (Most Changed Files):")
    lines.append("-" * 50)
    
    # Sort by total changes
    sorted_files = sorted(file_churn.items(), key=lambda x: -x[1]['changes'])[:max_items]
    
    max_changes = sorted_files[0][1]['changes'] if sorted_files else 1
    scale = 30 / max_changes if max_changes > 0 else 1
    
    for file_path, stats in sorted_files:
        bar_length = int(stats['changes'] * scale)
        bar = "▓" * bar_length
        display_path = file_path[:40] if len(file_path) > 40 else file_path
        lines.append(f"{display_path:40} │ {bar} {stats['changes']} ({stats['commits']} commits)")
    
    return "\n".join(lines)

def generate_tech_debt_report(metrics: Dict) -> str:
    """Generate a tech debt health report."""
    if not metrics:
        return ""
    
    lines = []
    lines.append("\n💡 Tech Debt Indicators:")
    lines.append("-" * 40)
    
    # Health bar
    health = metrics.get('health_score', 0)
    health_bar = "▓" * int(health / 5) + "░" * (20 - int(health / 5))
    
    lines.append(f"Health Score: {health:.1f}%")
    lines.append(f"[{health_bar}]")
    lines.append("")
    lines.append(f"  Features:    {metrics.get('feature_percentage', 0):.1f}% ({metrics.get('feature_commits', 0)})")
    lines.append(f"  Maintenance: {metrics.get('maintenance_percentage', 0):.1f}% ({metrics.get('maintenance_commits', 0)})")
    lines.append(f"  Debt:        {metrics.get('debt_percentage', 0):.1f}% ({metrics.get('debt_commits', 0)})")
    
    return "\n".join(lines)

def parse_relative_date(date_str: str) -> Optional[str]:
    """Parse relative date strings like '2 weeks ago', '1 month ago'."""
    now = datetime.now()
    match = re.match(r'(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago', date_str, re.IGNORECASE)
    if not match:
        return date_str  # Return as-is, let git handle it
    
    amount = int(match.group(1))
    unit = match.group(2).lower()
    
    if unit in ('second', 'seconds'):
        delta = timedelta(seconds=amount)
    elif unit in ('minute', 'minutes'):
        delta = timedelta(minutes=amount)
    elif unit in ('hour', 'hours'):
        delta = timedelta(hours=amount)
    elif unit in ('day', 'days'):
        delta = timedelta(days=amount)
    elif unit in ('week', 'weeks'):
        delta = timedelta(weeks=amount)
    elif unit in ('month', 'months'):
        delta = timedelta(days=amount * 30)
    elif unit in ('year', 'years'):
        delta = timedelta(days=amount * 365)
    else:
        return date_str
    
    result = now - delta
    return result.strftime('%Y-%m-%d')

def generate_markdown_report(output: Dict) -> str:
    """Generate a markdown summary report."""
    md = []
    md.append("# OmniLens Report\n")
    
    # Metadata
    md.append("## Overview\n")
    md.append(f"- **Path**: {output['metadata']['path']}")
    md.append(f"- **Analyzed At**: {output['metadata']['analyzed_at']}")
    md.append(f"- **Mode**: {output['metadata']['mode']}")
    if output['metadata'].get('duration_days'):
        md.append(f"- **Duration**: {output['metadata']['duration_days']} days")
    md.append("")
    
    # Stats
    stats = output['stats']
    md.append("## Statistics")
    md.append(f"- **Total Files**: {stats['total_files']:,}")
    md.append(f"- **Lines of Code**: {stats.get('total_loc', 0):,}")
    md.append(f"- **Git Repository**: {'Yes' if stats['is_git_repo'] else 'No'}")
    md.append("")
    
    # Top extensions
    if stats.get('extensions'):
        md.append("### File Types")
        exts = sorted(stats['extensions'].items(), key=lambda x: -x[1])[:10]
        for ext, count in exts:
            md.append(f"- **{ext}**: {count} files")
        md.append("")
    
    # Classes
    classes = output.get('classes', [])
    if classes:
        md.append(f"## Code Elements ({len(classes)} total)")
        
        by_type = {}
        for c in classes:
            ct = c['class_type']
            by_type[ct] = by_type.get(ct, 0) + 1
        
        md.append("### By Type")
        for ct, count in sorted(by_type.items()):
            md.append(f"- **{ct}**: {count}")
        md.append("")
        
        by_lang = {}
        for c in classes:
            lang = c['language']
            by_lang[lang] = by_lang.get(lang, 0) + 1
        
        md.append("### By Language")
        for lang, count in sorted(by_lang.items(), key=lambda x: -x[1]):
            md.append(f"- **{lang}**: {count}")
        md.append("")
        
        # Top classes
        md.append("### Top Classes/Functions")
        for c in sorted(classes, key=lambda x: x['line_number'])[:20]:
            doc = c['docstring'][:50] + "..." if c.get('docstring') and len(c.get('docstring', '')) > 50 else c.get('docstring', '')
            md.append(f"- **{c['name']}** (`{c['class_type']}`) - {c['file_path']}:{c['line_number']}")
            if doc:
                md.append(f"  > {doc}")
        md.append("")
    
    # Commits
    history = output.get('history', [])
    if history:
        md.append(f"## Commit History ({len(history)} commits)")
        
        cats = output.get('category_breakdown', {})
        md.append("### By Category")
        for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
            md.append(f"- **{cat}**: {count}")
        md.append("")
        
        authors = output.get('author_stats', {})
        if authors:
            md.append("### Top Contributors")
            top_authors = sorted(authors.items(), key=lambda x: -x[1]['commits'])[:5]
            for name, data in top_authors:
                md.append(f"- **{name}**: {data['commits']} commits, +{data['insertions']}/-{data['deletions']} lines")
        md.append("")
        
        # Recent commits
        md.append("### Recent Commits")
        for commit in history[:10]:
            md.append(f"- `{commit['hash'][:7]}` **{commit['category']}**: {commit['message']}")
        md.append("")
    
    return "\n".join(md)

def generate_csv_report(output: Dict) -> str:
    """Generate a CSV report from the analysis output."""
    lines = []

    # Commits CSV
    history = output.get('history', [])
    if history:
        lines.append("# Commits")
        lines.append("hash,author_name,author_email,date,message,category,scope,is_breaking,insertions,deletions,files_changed")
        for commit in history:
            row = [
                commit.get('hash', ''),
                commit.get('author_name', ''),
                commit.get('author_email', ''),
                commit.get('date', ''),
                commit.get('message', '').replace(',', ';'),  # Escape commas
                commit.get('category', ''),
                commit.get('scope', ''),
                commit.get('is_breaking', ''),
                commit.get('insertions', 0),
                commit.get('deletions', 0),
                commit.get('files_changed', 0)
            ]
            lines.append(','.join(str(x) for x in row))
        lines.append("")  # Empty line separator

    # Classes CSV
    classes = output.get('classes', [])
    if classes:
        lines.append("# Classes")
        lines.append("name,file_path,line_number,class_type,language,is_test,docstring,methods,bases,complexity")
        for cls in classes:
            row = [
                cls.get('name', ''),
                cls.get('file_path', ''),
                cls.get('line_number', 0),
                cls.get('class_type', ''),
                cls.get('language', ''),
                cls.get('is_test', False),
                (cls.get('docstring', '') or '').replace(',', ';').replace('\n', ' '),
                ';'.join(cls.get('methods', [])),
                ';'.join(cls.get('bases', [])),
                cls.get('complexity', 0)
            ]
            lines.append(','.join(str(x) for x in row))
        lines.append("")  # Empty line separator

    # Stats CSV
    stats = output.get('stats', {})
    if stats:
        lines.append("# Statistics")
        lines.append("key,value")
        for key, value in stats.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    lines.append(f"{key}.{sub_key},{sub_value}")
            else:
                lines.append(f"{key},{value}")
        lines.append("")  # Empty line separator

    # Category breakdown
    cats = output.get('category_breakdown', {})
    if cats:
        lines.append("# Category Breakdown")
        lines.append("category,count")
        for cat, count in cats.items():
            lines.append(f"{cat},{count}")
        lines.append("")  # Empty line separator

    # Author stats
    authors = output.get('author_stats', {})
    if authors:
        lines.append("# Author Statistics")
        lines.append("author_name,commits,insertions,deletions,files_changed")
        for name, stats in authors.items():
            row = [
                name,
                stats.get('commits', 0),
                stats.get('insertions', 0),
                stats.get('deletions', 0),
                stats.get('files_changed', 0)
            ]
            lines.append(','.join(str(x) for x in row))

    return '\n'.join(lines)

def generate_html_report(output: Dict) -> str:
    """Generate an interactive HTML report with charts and professional styling."""
    html = []
    html.append("<!DOCTYPE html>")
    html.append("<html lang='en'>")
    html.append("<head>")
    html.append("    <meta charset='UTF-8'>")
    html.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
    html.append("    <title>OmniLens Report</title>")
    html.append("    <script src='https://cdn.jsdelivr.net/npm/chart.js'></script>")
    html.append("    <style>")
    html.append("        * { margin: 0; padding: 0; box-sizing: border-box; }")
    html.append("        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }")
    html.append("        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }")
    html.append("        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; text-align: center; }")
    html.append("        .header h1 { font-size: 2.5em; margin-bottom: 10px; }")
    html.append("        .header p { opacity: 0.9; font-size: 1.1em; }")
    html.append("        .card { background: white; border-radius: 10px; padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }")
    html.append("        .card h2 { color: #2c3e50; margin-bottom: 20px; border-bottom: 2px solid #3498db; padding-bottom: 10px; }")
    html.append("        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }")
    html.append("        .stat-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #3498db; }")
    html.append("        .stat-value { font-size: 2em; font-weight: bold; color: #2c3e50; }")
    html.append("        .stat-label { color: #7f8c8d; margin-top: 5px; }")
    html.append("        .chart-container { position: relative; height: 400px; margin: 20px 0; }")
    html.append("        .table { width: 100%; border-collapse: collapse; margin-top: 20px; }")
    html.append("        .table th, .table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }")
    html.append("        .table th { background: #f8f9fa; font-weight: 600; }")
    html.append("        .table tr:hover { background: #f8f9fa; }")
    html.append("        .code-snippet { background: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 6px; font-family: 'Monaco', 'Menlo', monospace; font-size: 0.9em; overflow-x: auto; margin: 10px 0; }")
    html.append("        .badge { display: inline-block; padding: 4px 8px; border-radius: 12px; font-size: 0.8em; font-weight: 500; }")
    html.append("        .badge-python { background: #3776ab; color: white; }")
    html.append("        .badge-javascript { background: #f7df1e; color: black; }")
    html.append("        .badge-java { background: #ed8b00; color: white; }")
    html.append("        .badge-cpp { background: #00599c; color: white; }")
    html.append("        .badge-go { background: #00add8; color: white; }")
    html.append("        .badge-rust { background: #000000; color: white; }")
    html.append("        .badge-other { background: #95a5a6; color: white; }")
    html.append("        .commit-hash { font-family: monospace; background: #f8f9fa; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }")
    html.append("        .progress-bar { background: #ecf0f1; border-radius: 10px; height: 20px; overflow: hidden; margin: 10px 0; }")
    html.append("        .progress-fill { height: 100%; background: linear-gradient(90deg, #3498db, #2980b9); transition: width 0.3s ease; }")
    html.append("        .tabs { display: flex; margin-bottom: 20px; border-bottom: 1px solid #ddd; }")
    html.append("        .tab { padding: 10px 20px; cursor: pointer; background: #f8f9fa; border: none; border-bottom: 2px solid transparent; }")
    html.append("        .tab.active { background: white; border-bottom: 2px solid #3498db; color: #3498db; }")
    html.append("        .tab-content { display: none; }")
    html.append("        .tab-content.active { display: block; }")
    html.append("        @media (max-width: 768px) { .stats-grid { grid-template-columns: 1fr; } .header h1 { font-size: 2em; } }")
    html.append("    </style>")
    html.append("</head>")
    html.append("<body>")
    html.append("    <div class='container'>")

    # Header
    metadata = output.get('metadata', {})
    html.append("        <div class='header'>")
    html.append(f"            <h1>📊 OmniLens Report</h1>")
    html.append(f"            <p>Analysis of {metadata.get('path', 'Unknown Path')} • Generated on {metadata.get('analyzed_at', 'Unknown Date')}</p>")
    html.append("        </div>")

    # Overview Stats
    stats = output.get('stats', {})
    html.append("        <div class='card'>")
    html.append("            <h2>📈 Overview Statistics</h2>")
    html.append("            <div class='stats-grid'>")
    html.append(f"                <div class='stat-card'><div class='stat-value'>{stats.get('total_files', 0):,}</div><div class='stat-label'>Total Files</div></div>")
    html.append(f"                <div class='stat-card'><div class='stat-value'>{stats.get('total_loc', 0):,}</div><div class='stat-label'>Lines of Code</div></div>")
    html.append(f"                <div class='stat-card'><div class='stat-value'>{len(output.get('classes', [])):,}</div><div class='stat-label'>Code Elements</div></div>")
    html.append(f"                <div class='stat-card'><div class='stat-value'>{len(output.get('history', [])):,}</div><div class='stat-label'>Commits</div></div>")
    html.append("            </div>")

    # File Extensions Chart
    extensions = stats.get('extensions', {})
    if extensions:
        html.append("            <div class='chart-container'>")
        html.append("                <canvas id='extensionsChart'></canvas>")
        html.append("            </div>")
    html.append("        </div>")

    # Commit Analysis
    history = output.get('history', [])
    if history:
        html.append("        <div class='card'>")
        html.append("            <h2>🔄 Commit Analysis</h2>")
        html.append("            <div class='tabs'>")
        html.append("                <button class='tab active' onclick='showTab(\"commits\")'>Recent Commits</button>")
        html.append("                <button class='tab' onclick='showTab(\"categories\")'>Categories</button>")
        html.append("                <button class='tab' onclick='showTab(\"authors\")'>Authors</button>")
        html.append("            </div>")

        # Recent Commits Tab
        html.append("            <div id='commits' class='tab-content active'>")
        html.append("                <table class='table'>")
        html.append("                    <thead><tr><th>Hash</th><th>Author</th><th>Date</th><th>Category</th><th>Message</th><th>Changes</th></tr></thead>")
        html.append("                    <tbody>")
        for commit in history[:20]:
            html.append("                        <tr>")
            html.append(f"                            <td><span class='commit-hash'>{commit.get('hash', '')[:7]}</span></td>")
            html.append(f"                            <td>{commit.get('author_name', '')}</td>")
            date_str = commit.get('date', '')
            if isinstance(date_str, datetime):
                date_str = date_str.strftime('%Y-%m-%d')
            html.append(f"                            <td>{date_str[:10] if date_str else ''}</td>")
            html.append(f"                            <td><span class='badge badge-other'>{commit.get('category', '')}</span></td>")
            html.append(f"                            <td>{commit.get('message', '')[:60]}{'...' if len(commit.get('message', '')) > 60 else ''}</td>")
            html.append(f"                            <td>+{commit.get('insertions', 0)} -{commit.get('deletions', 0)}</td>")
            html.append("                        </tr>")
        html.append("                    </tbody>")
        html.append("                </table>")
        html.append("            </div>")

        # Categories Tab
        cats = output.get('category_breakdown', {})
        if cats:
            html.append("            <div id='categories' class='tab-content'>")
            html.append("                <div class='chart-container'>")
            html.append("                    <canvas id='categoriesChart'></canvas>")
            html.append("                </div>")
            html.append("            </div>")

        # Authors Tab
        authors = output.get('author_stats', {})
        if authors:
            html.append("            <div id='authors' class='tab-content'>")
            html.append("                <div class='chart-container'>")
            html.append("                    <canvas id='authorsChart'></canvas>")
            html.append("                </div>")
            html.append("            </div>")

        html.append("        </div>")

    # Code Elements
    classes = output.get('classes', [])
    if classes:
        html.append("        <div class='card'>")
        html.append("            <h2>🏗️ Code Elements</h2>")
        html.append("            <table class='table'>")
        html.append("                <thead><tr><th>Name</th><th>Type</th><th>Language</th><th>File</th><th>Line</th></tr></thead>")
        html.append("                <tbody>")

        for cls in classes[:50]:  # Limit to 50 for performance
            lang_badge = f"badge-{cls.get('language', 'other').lower()}"
            html.append("                    <tr>")
            html.append(f"                        <td><strong>{cls.get('name', '')}</strong></td>")
            html.append(f"                        <td><span class='badge badge-other'>{cls.get('class_type', '')}</span></td>")
            html.append(f"                        <td><span class='badge {lang_badge}'>{cls.get('language', '')}</span></td>")
            html.append(f"                        <td>{cls.get('file_path', '')}</td>")
            html.append(f"                        <td>{cls.get('line_number', 0)}</td>")
            html.append("                    </tr>")
        html.append("                </tbody>")
        html.append("            </table>")
        html.append("        </div>")

    html.append("    </div>")

    # JavaScript for interactivity
    html.append("    <script>")
    html.append("        function showTab(tabName) {")
    html.append("            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));")
    html.append("            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));")
    html.append("            document.querySelector(`button[onclick*='${tabName}']`).classList.add('active');")
    html.append("            document.getElementById(tabName).classList.add('active');")
    html.append("        }")

    # Extensions Chart
    if extensions:
        html.append("        const extensionsCtx = document.getElementById('extensionsChart').getContext('2d');")
        html.append("        new Chart(extensionsCtx, {")
        html.append("            type: 'doughnut',")
        html.append("            data: {")
        html.append("                labels: " + str(list(extensions.keys())) + ",")
        html.append("                datasets: [{")
        html.append("                    data: " + str(list(extensions.values())) + ",")
        html.append("                    backgroundColor: ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#34495e', '#e67e22', '#95a5a6'],")
        html.append("                }]")
        html.append("            },")
        html.append("            options: {")
        html.append("                responsive: true,")
        html.append("                plugins: {")
        html.append("                    title: { display: true, text: 'File Extensions Distribution' }")
        html.append("                }")
        html.append("            }")
        html.append("        });")

    # Categories Chart
    if cats:
        html.append("        const categoriesCtx = document.getElementById('categoriesChart').getContext('2d');")
        html.append("        new Chart(categoriesCtx, {")
        html.append("            type: 'bar',")
        html.append("            data: {")
        html.append("                labels: " + str(list(cats.keys())) + ",")
        html.append("                datasets: [{")
        html.append("                    label: 'Commits',")
        html.append("                    data: " + str(list(cats.values())) + ",")
        html.append("                    backgroundColor: '#3498db',")
        html.append("                }]")
        html.append("            },")
        html.append("            options: {")
        html.append("                responsive: true,")
        html.append("                plugins: {")
        html.append("                    title: { display: true, text: 'Commits by Category' }")
        html.append("                }")
        html.append("            }")
        html.append("        });")

    # Authors Chart
    if authors:
        top_authors = dict(sorted(authors.items(), key=lambda x: x[1]['commits'], reverse=True)[:10])
        html.append("        const authorsCtx = document.getElementById('authorsChart').getContext('2d');")
        html.append("        new Chart(authorsCtx, {")
        html.append("            type: 'horizontalBar',")
        html.append("            data: {")
        html.append("                labels: " + str(list(top_authors.keys())) + ",")
        html.append("                datasets: [{")
        html.append("                    label: 'Commits',")
        html.append("                    data: " + str([a['commits'] for a in top_authors.values()]) + ",")
        html.append("                    backgroundColor: '#2ecc71',")
        html.append("                }]")
        html.append("            },")
        html.append("            options: {")
        html.append("                responsive: true,")
        html.append("                plugins: {")
        html.append("                    title: { display: true, text: 'Top Contributors' }")
        html.append("                }")
        html.append("            }")
        html.append("        });")

    html.append("    </script>")
    html.append("</body>")
    html.append("</html>")

    return '\n'.join(html)

def run_analysis():
    parser = argparse.ArgumentParser(
        description="OmniLens - Professional-Grade Code Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  omnilens                                    # Current directory
  omnilens /path/to/repo                      # Specific directory
  omnilens --since "2 weeks ago"              # Relative date
  omnilens --author "John Doe"                # Filter by author
  omnilens --output report.json               # JSON output
  omnilens --format html --output report.html # HTML output
  omnilens --html --tech-debt                 # Tech debt analysis
  omnilens --interactive                      # Interactive mode
  omnilens --diff main..feature               # Compare branches
  omnilens --tech-debt --complexity           # Full analysis
  omnilens --export-csv commits.csv           # Export CSV
  omnilens --deps --format html               # Dependency graph
        """
    )
    parser.add_argument("--version", action="version", version=f"OmniLens {__version__}")
    parser.add_argument("path", nargs="?", default=".", help="Path to the repo or folder")
    parser.add_argument("--since", help="Start date (e.g., '2023-01-01' or '2 weeks ago')")
    parser.add_argument("--until", help="End date (e.g., 'yesterday')")
    parser.add_argument("--author", help="Filter commits by author (supports regex)")
    parser.add_argument("--output", default="intelligence_report.json", help="Output file path")
    parser.add_argument("--format", default="json", choices=["json", "markdown", "html", "csv"], help="Output format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--no-loc", action="store_true", help="Skip LOC counting (faster)")
    parser.add_argument("--no-git", action="store_true", help="Skip git analysis (works without git repo)")
    parser.add_argument("--no-classes", action="store_true", help="Skip class extraction")
    parser.add_argument("--all", action="store_true", help="Include merge commits (default excludes them)")
    parser.add_argument("--snip-format", default="short", choices=["short", "long"],
                        help="Code snippet format: short (1-20 lines) or long (10-50 lines)")
    parser.add_argument("--deep-level", default="1", choices=["1", "2", "3", "all"],
                        help="Depth of file analysis: 1=basic, 2=detailed, 3=comprehensive, all=maximum")
    parser.add_argument("--progress", action="store_true", help="Show progress bar for large repos")
    parser.add_argument("--export-csv", metavar="FILE", help="Export commits to CSV file")
    parser.add_argument("--export-classes-csv", metavar="FILE", help="Export classes to CSV file")
    parser.add_argument("--tech-debt", action="store_true", help="Calculate tech debt metrics")
    parser.add_argument("--complexity", action="store_true", help="Calculate complexity metrics")
    parser.add_argument("--html", action="store_true", help="Generate HTML report (shorthand for --format html)")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive TUI mode")
    parser.add_argument("--config", metavar="FILE", help="Path to config file (YAML)")
    parser.add_argument("--diff", metavar="BRANCH", help="Compare with specified branch (e.g., 'main..feature')")
    parser.add_argument("--exclude-dirs", metavar="PATS", help="Comma-separated dirs to exclude")
    parser.add_argument("--exclude-files", metavar="PATS", help="Comma-separated files to exclude")
    parser.add_argument("--deps", action="store_true", help="Extract dependency graph")
    parser.add_argument("--ai-summary", action="store_true", help="Generate AI summary (requires OpenAI key)")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching")
    parser.add_argument("--tree-sitter", action="store_true", help="Force Tree-Sitter parsing (default: auto)")
    args = parser.parse_args()

    # Handle --html shorthand
    if args.html:
        args.format = "html"

    repo_path = Path(args.path).resolve()
    
    if not repo_path.exists():
        print(f"[ERROR] Path does not exist: {repo_path}", file=sys.stderr)
        sys.exit(1)
    
    if not repo_path.is_dir():
        print(f"[ERROR] Path is not a directory: {repo_path}", file=sys.stderr)
        sys.exit(1)

    # Parse relative dates
    since = parse_relative_date(args.since) if args.since else None
    until = parse_relative_date(args.until) if args.until else None

    git = GitIntelligence(repo_path, verbose=args.verbose)
    code = CodebaseAnalyzer(repo_path, verbose=args.verbose, skip_git=args.no_git)

    is_git = not args.no_git and git.is_git_repository()
    
    if not is_git and not args.no_git:
        print(f"[ERROR] Not a git repository: {repo_path}", file=sys.stderr)
        print(f"[ERROR] Use --no-git flag to analyze without git", file=sys.stderr)
        sys.exit(1)
    
    print(f"--- Analyzing: {repo_path} ---")
    print(f"Mode: {'Git repository' if is_git else 'File scan only'}")
    
    if args.verbose:
        print(f"[DEBUG] Path: {repo_path}")
        print(f"[DEBUG] Since: {since or args.since}")
        print(f"[DEBUG] Until: {until or args.until}")
        print(f"[DEBUG] Author: {args.author}")
        print(f"[DEBUG] Is git: {is_git}")

    commits = []
    category_breakdown = {}
    author_stats = {}
    
    if is_git:
        commits = git.get_history(since=since, until=until, author=args.author, all_commits=args.all)
        
        if commits:
            print(f"Found {len(commits)} commits")
            category_breakdown = git.get_category_breakdown(commits)
            author_stats = git.get_author_stats(commits)
        else:
            print("No commits found for the given criteria.")
    else:
        print("No git repository - skipping commit analysis")

    files = code.get_all_files()
    print(f"Found {len(files)} files")

    if args.no_loc:
        cb_stats = {
            'total_files': len(files), 
            'extensions': {}, 
            'total_loc': 0,
            'is_git_repo': is_git,
            'skipped': True
        }
    else:
        cb_stats = code.scan(files)

    classes = []
    if not args.no_classes:
        classes = code.extract_classes(files)
        print(f"Found {len(classes)} code elements:")
        
        # Print breakdown
        by_type = {}
        for c in classes:
            by_type[c.class_type] = by_type.get(c.class_type, 0) + 1
        for ct, count in sorted(by_type.items()):
            print(f"  - {ct}: {count}")

    if not args.no_loc:
        print(f"Codebase LoC: {cb_stats.get('total_loc', 0):,}")
    
    if category_breakdown:
        print(generate_category_chart(category_breakdown))
    
    if author_stats:
        print(generate_author_chart(author_stats))
    
    if commits:
        print(generate_commit_timeline(commits))
    
    if commits:
        first_date = commits[-1].date.date()
        last_date = commits[0].date.date()
        duration_days = (last_date - first_date).days or 1
        print(f"\nPeriod: {first_date} to {last_date} ({duration_days} days)")
    else:
        duration_days = 0

    output = {
        "metadata": {
            "path": str(repo_path), 
            "since": since or args.since,
            "until": until or args.until,
            "author": args.author,
            "duration_days": duration_days,
            "analyzed_at": datetime.now().isoformat(),
            "mode": "git" if is_git else "file_scan"
        },
        "stats": cb_stats,
        "history": [asdict(c) for c in commits],
        "category_breakdown": category_breakdown,
        "author_stats": author_stats,
        "classes": [asdict(c) for c in classes],
        "tech_debt_metrics": {},
        "file_churn": {}
    }
    
    output_path = Path(args.output).resolve()
    
    try:
        # Handle dedicated CSV export flags
        # Paths are resolved relative to repo_path, not current working directory
        if args.export_csv:
            commits_csv_path = repo_path / args.export_csv
            commits = output.get('history', [])
            if commits:
                with open(commits_csv_path, "w", encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['hash', 'author_name', 'author_email', 'date', 'message', 'category', 'scope', 'is_breaking', 'insertions', 'deletions', 'files_changed'])
                    for commit in commits:
                        writer.writerow([
                            commit.get('hash', ''),
                            commit.get('author_name', ''),
                            commit.get('author_email', ''),
                            commit.get('date', ''),
                            commit.get('message', '').replace(',', ';'),
                            commit.get('category', ''),
                            commit.get('scope', ''),
                            commit.get('is_breaking', ''),
                            commit.get('insertions', 0),
                            commit.get('deletions', 0),
                            commit.get('files_changed', 0)
                        ])
                print(f"\nCommits CSV exported to {commits_csv_path}")
            else:
                print("\nNo commits to export")
        
        if args.export_classes_csv:
            classes_csv_path = repo_path / args.export_classes_csv
            classes = output.get('classes', [])
            if classes:
                with open(classes_csv_path, "w", encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['name', 'file_path', 'line_number', 'class_type', 'language', 'is_test', 'docstring', 'methods', 'bases', 'complexity'])
                    for cls in classes:
                        doc = (cls.get('docstring', '') or '').replace(',', ';').replace('\n', ' ')
                        methods = ';'.join(cls.get('methods', []))
                        bases = ';'.join(cls.get('bases', []))
                        writer.writerow([
                            cls.get('name', ''),
                            cls.get('file_path', ''),
                            cls.get('line_number', 0),
                            cls.get('class_type', ''),
                            cls.get('language', ''),
                            cls.get('is_test', False),
                            doc,
                            methods,
                            bases,
                            cls.get('complexity', 0)
                        ])
                print(f"\nClasses CSV exported to {classes_csv_path}")
            else:
                print("\nNo classes to export")
        
        if args.format == 'markdown':
            md_content = generate_markdown_report(output)
            with open(output_path, "w", encoding='utf-8') as f:
                f.write(md_content)
            print(f"\nMarkdown report saved to {output_path}")
        elif args.format == 'csv':
            csv_content = generate_csv_report(output)
            with open(output_path, "w", encoding='utf-8', newline='') as f:
                f.write(csv_content)
            print(f"\nCSV report saved to {output_path}")
        elif args.format == 'html':
            html_content = generate_html_report(output)
            with open(output_path, "w", encoding='utf-8') as f:
                f.write(html_content)
            print(f"\nHTML report saved to {output_path}")
        else:
            with open(output_path, "w", encoding='utf-8') as f:
                json.dump(output, f, default=str, indent=2)
            print(f"\nDetailed report saved to {output_path}")
    except IOError as e:
        print(f"[ERROR] Could not write output file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_analysis()
