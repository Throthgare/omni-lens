# TODO: Add Report Generation Functions

## Plan
1. Add `generate_csv_report` function after `generate_tech_debt_report`
2. Add `generate_html_report` function after `generate_markdown_report`

## Functions to Implement

### 1. generate_csv_report (after generate_tech_debt_report)
Generate a CSV report from analysis output with:
- Commit history
- Category breakdown
- Author statistics

### 2. generate_html_report (after generate_markdown_report)
Generate an HTML report with:
- Professional styling
- Charts and visualizations
- Interactive elements

## Status
- [x] Implement generate_csv_report
- [x] Implement generate_html_report
- [x] Test the new functions

# TODO List - OmniLens
+# TODO - Add CSV and HTML Report Functions
  
-## Implementation Phases
+## Task
+Add `generate_csv_report` and `generate_html_report` functions to `commit_gather_script.py`
  
----
+## Plan
+1. Add `generate_csv_report(output: Dict, output_type: str = 'commits') -> str` function
+   - Generate CSV format for commits data
+   - Support exporting classes data as CSV
+   - Return CSV string
+   
+2. Add `generate_html_report(output: Dict) -> str` function
+   - Generate interactive HTML report with charts
+   - Include CSS styling
+   - Include JavaScript for interactivity
  
-## Phase 1: Core Infrastructure & Tree-Sitter Parsing
-**Goal**: Replace regex with Tree-Sitter for 10x more accurate class/function detection
+## Progress
+- [ ] Add `generate_csv_report` function
+- [ ] Add `generate_html_report` function
+- [ ] Test the new functions
  
-### 1.1 Tree-Sitter Setup
-- [ ] Add tree-sitter dependencies
-- [ ] Create language builder utility
-- [ ] Pre-load grammars (Python, JavaScript, TypeScript, Java, C++, Go, Rust, Ruby, PHP, C#)
-- [ ] Implement `TreeSitterParser` class
-
-### 1.2 Enhanced Parsing
-- [ ] Extract functions with accurate signature parsing
-- [ ] Extract classes with proper inheritance detection
-- [ ] Extract methods with decorators support
-- [ ] Handle async/await properly
-- [ ] Support generics/type parameters
-- [ ] Extract docstrings/comments
-
-### 1.3 Complexity Metrics
-- [ ] Implement cyclomatic complexity calculation
-- [ ] Calculate maintainability index
-- [ ] Add complexity to ClassInfo dataclass
-- [ ] Add `--complexity` CLI flag
-
-### 1.4 Progress Bar
-- [ ] Add tqdm import
-- [ ] Add progress display for file scanning
-- [ ] Add progress display for class extraction
-- [ ] Add progress display for git history parsing
-- [ ] Add `--progress` CLI flag
-
----
-
-## Phase 2: HTML Reports & Interactive Charts
-**Goal**: Transform from terminal tool to shareable presentation-ready reports
-
-### 2.1 HTML Report Generator
-- [ ] Create HTML template with CSS styling
-- [ ] Add category pie chart (Chart.js/Plotly)
-- [ ] Add commit timeline line chart
-- [ ] Add author contribution bar chart
-- [ ] Add hotspot heatmap
-- [ ] Add code snippets with syntax highlighting (highlight.js)
-- [ ] Add tech debt section with health score
-
-### 2.2 Enhanced Output
-- [ ] Add `--html` CLI flag
-- [ ] Add `--format html` CLI option
-- [ ] Support `--output` for HTML files
-- [ ] Add responsive design for mobile viewing
-
----
-
-## Phase 3: Tech Debt & Metrics
-**Goal**: Real insights instead of placeholders
-
-### 3.1 Tech Debt Metrics
-- [ ] Implement `calculate_tech_debt_metrics()`
-- [ ] Calculate feature vs maintenance vs debt ratio
-- [ ] Implement health score calculation
-- [ ] Add `--tech-debt` CLI flag
-
-### 3.2 Code Ownership Metrics
-- [ ] Implement bus factor calculation
-- [ ] Calculate % commits per author per file
-- [ ] Identify code hotspots by ownership concentration
-
-### 3.3 Duplication Detection
-- [ ] Implement n-gram overlap detection
-- [ ] Identify duplicate functions
-- [ ] Add duplication hints to report
-
----
-
-## Phase 4: Caching & Performance
-**Goal**: Speed & UX improvements
-
-### 4.1 Caching System
-- [ ] Create `.codebase_intel_cache/` directory
-- [ ] Implement cache key generation (args + git HEAD hash)
-- [ ] Cache parsed results
-- [ ] Invalidate cache on file changes
-- [ ] Add `--no-cache` CLI flag
-
-### 4.2 Exclude Patterns
-- [ ] Define DEFAULT_EXCLUDE_DIRS (50+ patterns)
-- [ ] Define DEFAULT_EXCLUDE_FILES
-- [ ] Add `--exclude-dirs` CLI option
-- [ ] Add `--exclude-files` CLI option
-- [ ] Implement pattern matching logic
-
----
-
-## Phase 5: Interactive TUI
-**Goal**: Rich interactive browsing experience
-
-### 5.1 Interactive TUI Implementation
-- [ ] Create `InteractiveTUI` class
-- [ ] Implement main menu navigation
-- [ ] Implement commits viewer with search
-- [ ] Implement category breakdown viewer
-- [ ] Implement contributor ranking
-- [ ] Implement file statistics viewer
-- [ ] Add `--interactive` / `-i` CLI flag
-
----
-
-## Phase 6: Advanced Features
-**Goal**: Professional-grade capabilities
-
-### 6.1 Diff Mode
-- [ ] Implement `compare_branches()` function
-- [ ] Add `--diff BRANCH` CLI flag
-- [ ] Show changed files between branches
-- [ ] Show commit differences
-- [ ] Generate diff summary
-
-### 6.2 Dependency Graph
-- [ ] Create `DependencyAnalyzer` class
-- [ ] Extract imports for all languages
-- [ ] Generate dependency edges
-- [ ] Add `--deps` CLI flag
-- [ ] Include Mermaid.js diagram in HTML report
-
-### 6.3 Test Coverage Hints
-- [ ] Detect test files automatically
-- [ ] Calculate test/src LOC ratio
-- [ ] Identify untested files
-- [ ] Add test coverage section to report
-
-### 6.4 AI Summary (Optional)
-- [ ] Add OpenAI integration (opt-in)
-- [ ] Create `--ai-summary` flag
-- [ ] Generate AI-powered summary
-- [ ] Handle API key configuration
-
----
-
-## Phase 7: Language Support & Parsing
-**Goal**: Extended language support
-
-### 7.1 Enhanced JS/TS Parsing
-- [ ] Add TypeScript interface extraction
-- [ ] Add TypeScript type alias extraction
-- [ ] Add enum extraction
-- [ ] Add async function detection
-- [ ] Better arrow function handling
-
-### 7.2 Ruby/PHP/C# Support
-- [ ] Add Ruby parser (class, module, method, require)
-- [ ] Add PHP parser (class, method, namespace, use)
-- [ ] Add C# parser (class, method, using)
-- [ ] Add Go parser (function, struct, import)
-
-### 7.3 Additional Languages
-- [ ] Add Kotlin/Scala support
-- [ ] Add Swift support
-- [ ] Add Dart support
-- [ ] Add Rust support (already partial)
-
----
-
-## Phase 8: Configuration & Packaging
-**Goal**: Professional packaging
-
-### 8.1 Config File Support
-- [ ] Create DEFAULT_CONFIG
-- [ ] Implement `load_config()` function
-- [ ] Support `.codebase-intel.yaml`
-- [ ] Add `--config` CLI flag
-- [ ] Merge config with CLI arguments
-
-### 8.2 CSV Export
-- [ ] Add `export_commits_csv()` function
-- [ ] Add `export_classes_csv()` function
-- [ ] Add `--export-csv` CLI flag
-- [ ] Add `--export-classes-csv` CLI flag
-
-### 8.3 Professional Packaging
-- [ ] Create `setup.py` / `pyproject.toml`
-- [ ] Add entry_points for CLI
-- [ ] Create pytest test suite
-- [ ] Add README with examples
-- [ ] Create ASCII logo
-
----
-
-## Testing & Validation
-
-### Unit Tests
-- [ ] Test Tree-Sitter parsing accuracy
-- [ ] Test complexity calculations
-- [ ] Test tech debt metrics
-- [ ] Test CSV export format
-- [ ] Test config file loading
-
-### Integration Tests
-- [ ] Test full analysis workflow
-- [ ] Test HTML report generation
-- [ ] Test interactive TUI
-- [ ] Test diff mode
-- [ ] Test with various repo sizes
-
-### Performance Tests
-- [ ] Test with large repos (1000+ files)
-- [ ] Test caching effectiveness
-- [ ] Test progress bar responsiveness
-
----
-
-## Completion Checklist
-
-### Core Features
-- [ ] Tree-Sitter parsing for accurate detection
-- [ ] Cyclomatic complexity per function/class
-- [ ] HTML report with interactive charts
-- [ ] Progress bar for large repos
-- [ ] Caching system
-
-### Metrics
-- [ ] Tech debt calculation
-- [ ] Code ownership metrics
-- [ ] Bus factor calculation
-- [ ] Duplication hints
-- [ ] Test coverage hints
-
-### Advanced Features
-- [ ] Interactive TUI mode
-- [ ] Diff mode for branch comparison
-- [ ] Dependency graph extraction
-- [ ] AI summary (opt-in)
-- [ ] Config file support
-
-### Language Support
-- [ ] Python (enhanced)
-- [ ] JavaScript/TypeScript (enhanced)
-- [ ] Ruby support
-- [ ] PHP support
-- [ ] C# support
-- [ ] Java/C++/Go/Rust (enhanced)
-
-### Output Formats
-- [ ] JSON (existing)
-- [ ] Markdown (existing)
-- [ ] HTML (new)
-- [ ] CSV (new)
-
-### Packaging
-- [ ] PyPI-ready package
-- [ ] Entry points configured
-- [ ] Test suite
-- [ ] README documentation
-- [ ] ASCII logo
-
----
-
-## Progress Tracking
-
-### ✅ Phase 1: In Progress
-- [ ] Tree-Sitter Setup
-- [ ] Enhanced Parsing
-- [ ] Complexity Metrics
-- [ ] Progress Bar
-
-### ⏳ Phase 2: Pending
-- [ ] HTML Report Generator
-- [ ] Enhanced Output
-
-### ⏳ Phase 3: Pending
-- [ ] Tech Debt Metrics
-- [ ] Code Ownership
-- [ ] Duplication Detection
-
-### ⏳ Phase 4: Pending
-- [ ] Caching System
-- [ ] Exclude Patterns
-
-### ⏳ Phase 5: Pending
-- [ ] Interactive TUI
-
-### ⏳ Phase 6: Pending
-- [ ] Diff Mode
-- [ ] Dependency Graph
-- [ ] Test Coverage
-- [ ] AI Summary
-
-### ⏳ Phase 7: Pending
-- [ ] Enhanced JS/TS
-- [ ] Ruby/PHP/C#
-- [ ] Additional Languages
-
-### ⏳ Phase 8: Pending
-- [ ] Config File
-- [ ] CSV Export
-- [ ] Packaging
-
----
-
-## Implementation Notes
-
-### Dependencies Required
-- `tree-sitter`
-- `tree-sitter-python`
-- `tree-sitter-javascript`
-- `tree-sitter-typescript`
-- `tree-sitter-java`
-- `tree-sitter-cpp`
-- `tree-sitter-go`
-- `tree-sitter-rust`
-- `tqdm`
-- `jinja2`
-- `pyyaml`
-- `openai` (optional, for AI summary)
-
-### Alternative (No External Dependencies)
-- Use regex fallback if Tree-Sitter not available
-- Use custom progress bar if tqdm not available
-- Use string templates if Jinja2 not available
-
-### Backward Compatibility
-- All existing CLI args must work
-- Output format must include all existing fields
-- Performance impact < 20% for small repos
-
----
-
-## Estimated Timeline
-
-| Phase | Features | Complexity | Estimated Time |
-|-------|----------|------------|----------------|
-| 1 | Tree-Sitter, Complexity, Progress | High | 2-3 hours |
-| 2 | HTML Reports | Medium | 1-2 hours |
-| 3 | Tech Debt, Ownership | Medium | 1 hour |
-| 4 | Caching, Exclude | Low | 30 min |
-| 5 | Interactive TUI | Medium | 1-2 hours |
-| 6 | Diff, Dependencies, AI | Medium | 2 hours |
-| 7 | Language Support | Medium | 1-2 hours |
-| 8 | Config, Packaging | Low | 1 hour |
-
-**Total Estimated Time**: 10-14 hours
-
----
-
-## Risk Assessment
-
-| Feature | Risk | Mitigation |
-|---------|------|------------|
-| Tree-Sitter parsing | Medium | Regex fallback available |
-| HTML report | Low | Template-based |
-| Tech debt metrics | Low | Simple math calculations |
-| Interactive TUI | Medium | Simple fallback mode |
-| AI Summary | High | Opt-in, handle errors gracefully |
-| Multi-language parsing | Medium | Progressive enhancement |
-| Caching | Low | Simple file-based cache |
-
----
-
-## Success Criteria
-
-1. **Accuracy**: 10x improvement in class/function detection
-2. **Performance**: < 2 min for 1000 files, < 5 min for 10000 files
-3. **Coverage**: All 15+ major languages supported
-4. **Reports**: HTML reports render in all major browsers
-5. **UX**: Progress bar shows during long operations
-6. **Stability**: Zero crashes on test corpus
-7. **Backward Compatibility**: 100% compatible with existing usage
-
+## Notes
+- File: commit_gather_script.py
+- Location: After `generate_tech_debt_report` for CSV
+- Location: After `generate_markdown_report` for HTML
