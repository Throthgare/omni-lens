# Implementation Plan - Phase 2 Enhancements

## Overview
This plan outlines the implementation of 13 major enhancements to OmniLens.

## Information Gathered

### Current State Analysis
- **Main Script**: `commit_gather_script.py` (1200+ lines)
- **Existing Features**:
  - Git history analysis with commit parsing
  - 80+ language extensions support
  - Basic class/function extraction via regex
  - JSON/Markdown output formats
  - Author stats and category breakdown
  - Breaking change detection (regex-based)
  - Test file detection patterns
  - ASCII visualization charts

### Missing Features (from TODO.md)
1. Better JS/TS parsing (arrow functions, interfaces)
2. Ruby, PHP, C# parsing support
3. Tech debt calculation
4. Progress bar for large repos
5. Better exclude patterns
6. CSV export
7. Import/dependency extraction
8. Complexity metrics
9. HTML report generation
10. Config file support (.codebase-intel.json)
11. Interactive TUI mode
12. Diff mode for comparing branches
13. Breaking change detection (already has some support)

---

## Plan: Implementation of All Requested Features

### Step 1: Enhanced JS/TS Parsing
**File**: `commit_gather_script.py`

**Changes**:
1. Add TypeScript interface/interface extraction regex patterns
2. Add better arrow function detection (handle `const fn = () => {}`, `export const fn = () => {}`)
3. Add TypeScript type extraction patterns
4. Add async arrow function detection
5. Add JSDoc parsing for better documentation extraction

**New Regex Patterns**:
```python
# TypeScript interfaces
INTERFACE_RE = re.compile(r'^(?:export\s+)?interface\s+(\w+)')

# Better arrow function detection
ARROW_FUNC_RE = re.compile(
    r'^(?:export\s+)?(?:const|let|var|async\s+)?(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>'
)

# TypeScript type definitions
TYPE_ALIAS_RE = re.compile(r'^(?:export\s+)?type\s+(\w+)\s*=')

# Enum extraction
ENUM_RE = re.compile(r'^(?:export\s+)?(?:const\s+)?enum\s+(\w+)')
```

### Step 2: Ruby, PHP, C# Parsing Support
**File**: `commit_gather_script.py`

**Ruby Parser**:
```python
RUBY_CLASS_RE = re.compile(r'^(?:class|module)\s+(\w+)(?:\s*<\s*([^\s]+))?')
RUBY_METHOD_RE = re.compile(r'^\s*def\s+(\w+)')
RUBY_ATTR_RE = re.compile(r'^\s*(attr_reader|attr_writer|attr_accessor)\s*:\s*(\w+)')
RUBY_REQUIRE_RE = re.compile(r'^\s*(?:require|require_relative)\s*[\'"](\S+)[\'"]')
```

**PHP Parser**:
```python
PHP_CLASS_RE = re.compile(r'^(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^\s{]+))?')
PHP_METHOD_RE = re.compile(r'^\s*(?:public|private|protected|static|\s)*function\s+(\w+)\s*\(')
PHP_NAMESPACE_RE = re.compile(r'^namespace\s+([^\s;]+);')
PHP_USE_RE = re.compile(r'^use\s+([^\s;]+);')
```

**C# Parser**:
```python
CSHARP_CLASS_RE = re.compile(
    r'^(?:public|private|internal|protected)\s+(?:static\s+)?(?:abstract\s+)?(?:class|interface|struct|enum)\s+(\w+)'
)
CSHARP_METHOD_RE = re.compile(
    r'^(?:public|private|internal|protected|static|async)\s+.*?\s+(\w+)\s*\('
)
CSHARP_USING_RE = re.compile(r'^using\s+([^\s;]+);')
```

### Step 3: Tech Debt Calculation
**File**: `commit_gather_script.py`

**Implementation**:
```python
def calculate_tech_debt_metrics(commits: List[CommitInfo]) -> Dict:
    """Calculate tech debt indicators from commit history."""
    total = len(commits)
    if total == 0:
        return {}
    
    # Categories that indicate debt
    debt_categories = ['chore', 'refactor', 'style', 'ci']
    # Categories that indicate new features
    feature_categories = ['feat', 'bugfix']
    # Categories that indicate maintenance
    maintenance_categories = ['docs', 'test']
    
    debt = sum(1 for c in commits if c.category in debt_categories)
    features = sum(1 for c in commits if c.category in feature_categories)
    maintenance = sum(1 for c in commits if c.category in maintenance_categories)
    
    # Health score based on feature/debt ratio
    health_score = min(100, (features / total) * 100 + 50) if total > 0 else 0
    
    return {
        'total_commits': total,
        'debt_commits': debt,
        'feature_commits': features,
        'maintenance_commits': maintenance,
        'debt_percentage': (debt / total) * 100 if total > 0 else 0,
        'feature_percentage': (features / total) * 100 if total > 0 else 0,
        'maintenance_percentage': (maintenance / total) * 100 if total > 0 else 0,
        'health_score': health_score
    }
```

### Step 4: Progress Bar for Large Repos
**File**: `commit_gather_script.py`

**Implementation**:
- Add `tqdm` import for progress bars
- Add `--progress` flag to enable/disable
- Add progress display for:
  - File scanning
  - Class extraction
  - Git history parsing
  - Report generation

### Step 5: Better Exclude Patterns
**File**: `commit_gather_script.py`

**Enhanced Exclude List**:
```python
DEFAULT_EXCLUDE_DIRS = [
    '.git', '__pycache__', 'node_modules', 'venv', '.venv',
    'build', 'dist', '.tox', '.nox', '.eggs', '*.egg-info',
    '.sass-cache', '.next', '.nuxt', '.output', '.cache',
    'coverage', '.nyc_output', '*.pyc', '*.pyo', '$py.class',
    '.mypy_cache', '.pytest_cache', '.hypothesis',
    'vendor', 'bower_components', '.idea', '.vscode',
    '*.swp', '*.swo', '*~', '.DS_Store', 'Thumbs.db',
    'target', 'Cargo.lock', 'package-lock.json', 'yarn.lock'
]

DEFAULT_EXCLUDE_FILES = [
    '*.min.js', '*.min.css', '*.map', '*.log', '*.lock',
    '.gitignore', '.gitattributes', '.editorconfig',
    '*.pem', '*.key', '*.crt', 'secrets.py'
]
```

### Step 6: CSV Export
**File**: `commit_gather_script.py`

**Implementation**:
```python
def export_commits_csv(commits: List[CommitInfo], output_path: str):
    """Export commits to CSV format."""
    import csv
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'hash', 'author', 'date', 'category', 'scope',
            'message', 'is_breaking', 'insertions', 'deletions', 'files_changed'
        ])
        writer.writeheader()
        for c in commits:
            writer.writerow({
                'hash': c.hash,
                'author': c.author_name,
                'date': c.date.isoformat(),
                'category': c.category,
                'scope': c.scope or '',
                'message': c.message,
                'is_breaking': c.is_breaking,
                'insertions': c.insertions,
                'deletions': c.deletions,
                'files_changed': c.files_changed
            })

def export_classes_csv(classes: List[ClassInfo], output_path: str):
    """Export classes to CSV format."""
    import csv
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'name', 'file_path', 'line_number', 'class_type',
            'language', 'is_test', 'complexity', 'methods_count'
        ])
        writer.writeheader()
        for c in classes:
            writer.writerow({
                'name': c.name,
                'file_path': c.file_path,
                'line_number': c.line_number,
                'class_type': c.class_type,
                'language': c.language,
                'is_test': c.is_test,
                'complexity': c.complexity,
                'methods_count': len(c.methods)
            })
```

### Step 7: Import/Dependency Extraction
**File**: `commit_gather_script.py`

**Implementation**:
```python
@dataclass
class ImportInfo:
    module: str
    alias: Optional[str]
    line_number: int
    import_type: str  # 'import', 'require', 'from', 'using', etc.

class DependencyAnalyzer:
    """Extract imports and dependencies from code files."""
    
    IMPORTS_PATTERNS = {
        'python': [
            (r'^import\s+(\w+(?:\.\w+)*)', 'import'),
            (r'^from\s+(\w+(?:\.\w+)*)\s+import', 'from'),
        ],
        'javascript': [
            (r'^import\s+.*?\s+from\s+[\'"](\S+)[\'"]', 'import'),
            (r'^import\s+[\'"](\S+)[\'"]', 'import'),
            (r'^const\s+(\w+)\s*=\s*require\([\'"](\S+)[\'"]', 'require'),
            (r'^require\([\'"](\S+)[\'"]', 'require'),
        ],
        'typescript': [
            (r'^import\s+.*?\s+from\s+[\'"](\S+)[\'"]', 'import'),
            (r'^import\s+[\'"](\S+)[\'"]', 'import'),
            (r'^require\([\'"](\S+)[\'"]', 'require'),
        ],
        'ruby': [
            (r'^\s*(require|require_relative)\s+[\'"](\S+)[\'"]', 'require'),
            (r'^\s*include\s+(\w+)', 'include'),
        ],
        'php': [
            (r'^\s*require(?:_once)?\s*[\'"](\S+)[\'"]', 'require'),
            (r'^\s*include(?:_once)?\s*[\'"](\S+)[\'"]', 'include'),
            (r'^use\s+(\S+);', 'use'),
        ],
        'csharp': [
            (r'^using\s+(\S+);', 'using'),
        ],
        'java': [
            (r'^import\s+(\S+);', 'import'),
        ],
        'go': [
            (r'^\s*import\s*\(\s*[\'"]([^\'"]+)[\'"]', 'import'),
        ],
    }
```

### Step 8: Complexity Metrics
**File**: `commit_gather_script.py`

**Implementation**:
```python
def calculate_cyclomatic_complexity(code: str) -> int:
    """Calculate cyclomatic complexity of a code block."""
    # Count decision points
    decision_points = [
        r'\bif\b', r'\belseif\b', r'\belse\b', r'\bfor\b',
        r'\bwhile\b', r'\bdo\b', r'\bcase\b', r'\bcatch\b',
        r'\b\?\b', r'\band\b', r'\bor\b', r'\b&&', r'\b\|\|',
    ]
    complexity = 1  # Base complexity
    for pattern in decision_points:
        complexity += len(re.findall(pattern, code))
    return complexity

def calculate_code_metrics(file_path: str, lines: List[str]) -> Dict:
    """Calculate various code metrics for a file."""
    code = ''.join(lines)
    
    # Remove comments for accurate counting
    stripped_code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
    stripped_code = re.sub(r'//.*$', '', stripped_code)
    stripped_code = re.sub(r'/\*.*?\*/', '', stripped_code, flags=re.DOTALL)
    
    loc = len([l for l in lines if l.strip() and not l.strip().startswith('#') and not l.strip().startswith('//')])
    sloc = len(stripped_code.split('\n'))
    
    # Count functions/methods
    functions = len(re.findall(r'(?:function|def|func|fn|method)\s+\w+', code))
    
    # Count classes
    classes = len(re.findall(r'(?:class|interface|struct)\s+\w+', code))
    
    # Calculate complexity
    complexity = calculate_cyclomatic_complexity(stripped_code)
    
    return {
        'loc': loc,
        'sloc': sloc,
        'functions': functions,
        'classes': classes,
        'complexity': complexity,
        'complexity_per_function': complexity / functions if functions > 0 else 0
    }
```

### Step 9: HTML Report Generation
**File**: `commit_gather_script.py`

**Implementation**:
```python
def generate_html_report(output: Dict) -> str:
    """Generate an interactive HTML report with charts."""
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Intelligence Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 10px 0; }}
        .stat {{ display: inline-block; margin: 10px 20px 10px 0; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .stat-label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; }}
        .chart-container {{ height: 300px; margin: 20px 0; }}
        .breaking {{ background: #ffebee; border-left: 4px solid #f44336; padding: 10px; margin: 5px 0; }}
        .feature {{ background: #e8f5e9; border-left: 4px solid #4caf50; padding: 10px; margin: 5px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Codebase Intelligence Report</h1>
        <p><strong>Path:</strong> {output['metadata']['path']}</p>
        <p><strong>Analyzed:</strong> {output['metadata']['analyzed_at']}</p>
        
        <!-- Overview Stats -->
        <div class="card">
            <h2>Overview</h2>
            <div class="stat">
                <div class="stat-value">{output['stats'].get('total_files', 0)}</div>
                <div class="stat-label">Files</div>
            </div>
            <div class="stat">
                <div class="stat-value">{output['stats'].get('total_loc', 0):,}</div>
                <div class="stat-label">Lines of Code</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(output.get('history', []))}</div>
                <div class="stat-label">Commits</div>
            </div>
        </div>
        
        <!-- Category Chart -->
        <div class="card">
            <h2>Commit Categories</h2>
            <div class="chart-container">
                <canvas id="categoryChart"></canvas>
            </div>
        </div>
        
        <!-- Tech Health -->
        {generate_health_section(output.get('tech_debt_metrics', {}))}
        
        <!-- Breaking Changes -->
        {generate_breaking_changes_section(output.get('history', []))}
        
        <!-- Top Contributors -->
        {generate_contributors_section(output.get('author_stats', {}))}
    </div>
    
    <script>
        // Chart.js initialization
        const categoryCtx = document.getElementById('categoryChart').getContext('2d');
        new Chart(categoryCtx, {{
            type: 'doughnut',
            data: {{
                labels: {list(output.get('category_breakdown', {}).keys())},
                datasets: [{{
                    data: {list(output.get('category_breakdown', {}).values())},
                    backgroundColor: ['#4caf50', '#f44336', '#2196f3', '#ff9800', '#9c27b0', '#00bcd4', '#607d8b']
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});
    </script>
</body>
</html>
    """
    return html
```

### Step 10: Config File Support
**File**: `commit_gather_script.py`

**Implementation**:
```python
CONFIG_FILE = ".codebase-intel.json"

DEFAULT_CONFIG = {
    "output": "intelligence_report.json",
    "format": "json",
    "since": None,
    "until": None,
    "author": None,
    "verbose": False,
    "no_loc": False,
    "no_git": False,
    "no_classes": False,
    "all_commits": False,
    "snip_format": "short",
    "deep_level": "1",
    "exclude_patterns": {
        "dirs": DEFAULT_EXCLUDE_DIRS,
        "files": DEFAULT_EXCLUDE_FILES
    },
    "enabled_features": {
        "progress_bar": True,
        "tech_debt": True,
        "complexity_metrics": True,
        "html_report": False,
        "csv_export": False
    }
}

def load_config(config_path: Path) -> Dict:
    """Load configuration from JSON file."""
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
            # Merge with defaults
            return {**DEFAULT_CONFIG, **config}
    return DEFAULT_CONFIG
```

### Step 11: Interactive TUI Mode
**File**: `commit_gather_script.py`

**Implementation** using standard library (no external dependencies):
```python
class InteractiveTUI:
    """Simple interactive TUI for browsing results."""
    
    def __init__(self, output: Dict):
        self.output = output
        self.current_view = 'main'
        self.selected_commit = 0
        self.scroll_offset = 0
    
    def run(self):
        """Main TUI loop."""
        try:
            import curses
            return self._run_curses()
        except ImportError:
            return self._run_simple()
    
    def _run_simple(self):
        """Simple interactive mode without curses."""
        print("\n🔍 Interactive Mode - Codebase Intelligence")
        print("=" * 50)
        
        while True:
            self._show_main_menu()
            choice = input("\nEnter choice (q to quit): ").strip()
            
            if choice == '1':
                self._show_commits()
            elif choice == '2':
                self._show_categories()
            elif choice == '3':
                self._show_contributors()
            elif choice == '4':
                self._show_files()
            elif choice.lower() == 'q':
                break
            else:
                print("Invalid choice")
    
    def _show_main_menu(self):
        """Display main menu."""
        print("\n📊 Codebase Intelligence - Main Menu")
        print("-" * 40)
        print("1. View Commits")
        print("2. Category Breakdown")
        print("3. Top Contributors")
        print("4. File Statistics")
        print("q. Quit")
```

### Step 12: Diff Mode for Comparing Branches
**File**: `commit_gather_script.py`

**Implementation**:
```python
def compare_branches(
    repo_path: Path,
    branch1: str,
    branch2: str,
    args
) -> Dict:
    """Compare two branches and generate diff report."""
    git = GitIntelligence(repo_path, verbose=args.verbose)
    
    # Get commits from each branch
    commits1 = git.get_history(since=args.since, until=args.until, author=args.author, all_commits=args.all)
    commits2 = git.get_history(since=args.since, until=args.until, author=args.author, all_commits=args.all)
    
    # Calculate diff
    set1 = {c.hash for c in commits1}
    set2 = {c.hash for c in commits2}
    
    added = [c for c in commits2 if c.hash not in set1]
    removed = [c for c in commits1 if c.hash not in set2]
    common = [c for c in commits1 if c.hash in set2]
    
    return {
        'branch1': branch1,
        'branch2': branch2,
        'added_commits': len(added),
        'removed_commits': len(removed),
        'common_commits': len(common),
        'added': [asdict(c) for c in added],
        'removed': [asdict(c) for c in removed],
        'category_diff': {
            'branch1': git.get_category_breakdown(commits1),
            'branch2': git.get_category_breakdown(commits2)
        }
    }
```

### Step 13: Enhanced Breaking Change Detection
**File**: `commit_gather_script.py`

**Implementation**:
```python
# Enhanced breaking change detection
BREAKING_RE = re.compile(r'BREAKING CHANGE[:\s]*(.+?)(?:\n\n|\n*$)?', re.IGNORECASE | re.DOTALL)
CONVENTIONAL_RE = re.compile(r'^(\w+)(?:\(([^)]+)\))?(!)?:\s*(.*)$')

def detect_breaking_changes(commits: List[CommitInfo]) -> List[Dict]:
    """Detect all breaking changes in commit history."""
    breaking = []
    for commit in commits:
        breaking_info = {
            'hash': commit.hash,
            'message': commit.message,
            'date': commit.date.isoformat(),
            'author': commit.author_name,
            'breaking_description': None
        }
        
        # Check for "!" in conventional commit
        if commit.is_breaking:
            breaking_info['breaking_description'] = commit.breaking_description
        
        # Check for BREAKING CHANGE in message
        match = BREAKING_RE.search(commit.full_message)
        if match:
            breaking_info['breaking_description'] = match.group(1).strip()
            breaking_info['type'] = 'breaking_change_annotation'
            breaking.append(breaking_info)
        elif commit.is_breaking:
            breaking_info['type'] = 'conventional_breaking'
            breaking.append(breaking_info)
    
    return breaking
```

---

## Files to Modify

### `commit_gather_script.py`
- Add all new imports (csv, typing extensions)
- Add new regex patterns for JS/TS, Ruby, PHP, C#
- Add `TechDebtCalculator` class
- Add `ProgressTracker` class
- Add `DependencyAnalyzer` class
- Add `ComplexityAnalyzer` class
- Add `HTMLReportGenerator` class
- Add `InteractiveTUI` class
- Add new command-line arguments
- Update `run_analysis()` to handle new options

---

## New Command-Line Arguments

```python
parser.add_argument("--progress", action="store_true", help="Show progress bar for large repos")
parser.add_argument("--format", default="json", choices=["json", "markdown", "html"], help="Output format")
parser.add_argument("--export-csv", metavar="FILE", help="Export commits to CSV")
parser.add_argument("--export-classes-csv", metavar="FILE", help="Export classes to CSV")
parser.add_argument("--diff", metavar="BRANCH", help="Compare current branch with specified branch")
parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive TUI mode")
parser.add_argument("--config", metavar="FILE", help="Path to config file (default: .codebase-intel.json)")
parser.add_argument("--exclude-dirs", metavar="PATTERNS", help="Comma-separated directory patterns to exclude")
parser.add_argument("--exclude-files", metavar="PATTERNS", help="Comma-separated file patterns to exclude")
parser.add_argument("--tech-debt", action="store_true", help="Calculate tech debt metrics")
parser.add_argument("--complexity", action="store_true", help="Calculate complexity metrics")
parser.add_argument("--html", action="store_true", help="Generate HTML report")
```

---

## Followup Steps

1. **Install dependencies**: None required (using standard library + optional Chart.js CDN for HTML)
2. **Testing**:
   - Test JS/TS parsing with test files
   - Test Ruby, PHP, C# parsing
   - Test progress bar with large repos
   - Test CSV export
   - Test HTML report generation
   - Test interactive TUI
   - Test diff mode
3. **Performance**: Add caching for repeated analysis
4. **Documentation**: Update help text and README

---

## Implementation Order

1. ✅ **Already Done**: Breaking change detection, test patterns, 80+ languages
2. **Next Phase**:
   - Step 1: Enhanced JS/TS parsing (priority - frequently used)
   - Step 2: Ruby, PHP, C# support (priority - common languages)
   - Step 3: Tech debt calculation (high value)
   - Step 4: Progress bar (UX improvement)
   - Step 5: Better exclude patterns (DX improvement)
   - Step 6: CSV export (data portability)
   - Step 7: Import/dependency extraction (insight)
   - Step 8: Complexity metrics (insight)
   - Step 9: HTML report (visualization)
   - Step 10: Config file (DX improvement)
   - Step 11: Interactive TUI (UX improvement)
   - Step 12: Diff mode (comparison feature)
   - Step 13: Enhanced breaking change detection (already partially done)

---

## Risk Assessment

| Feature | Complexity | Risk | Mitigation |
|---------|-----------|------|------------|
| JS/TS parsing | Medium | Low | Regex-based, well-tested patterns |
| Ruby/PHP/C# | Medium | Medium | Need test files for validation |
| Tech debt | Low | Low | Simple math calculation |
| Progress bar | Low | Low | Standard library only |
| Exclude patterns | Low | Low | Extend existing patterns |
| CSV export | Low | Low | Standard library csv module |
| Dependencies | Medium | Medium | Pattern-based extraction |
| Complexity metrics | Medium | Medium | Regex-based estimation |
| HTML report | Medium | Low | Template-based generation |
| Config file | Low | Low | Standard JSON parsing |
| TUI | High | Medium | Simple fallback available |
| Diff mode | Medium | Medium | Need branch comparison testing |
| Breaking changes | Low | Low | Already implemented |

---

## Success Criteria

1. All 13 features implemented and functional
2. Backward compatibility maintained (existing CLI args work)
3. Test coverage maintained or improved
4. Performance impact minimal (< 20% slowdown)
5. HTML reports render correctly in major browsers
6. TUI works without external dependencies

