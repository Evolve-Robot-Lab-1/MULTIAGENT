# CLAUDE.md - Model Behavior Guidelines for DocAI Native Development

## Core Principles for Model Behavior

### 1. Context Awareness
- **Always read relevant files** before making changes
- **Understand the full architecture** before implementing features
- **Check for existing implementations** before creating new ones
- **Verify dependencies** exist before using them

### 2. Systematic Approach
When implementing any feature:
1. **Analyze** - Read existing code and understand current state
2. **Plan** - Create detailed execution plan before coding
3. **Implement** - Follow the plan systematically
4. **Verify** - Test each component as you build
5. **Document** - Update relevant documentation immediately

### 3. Code Quality Standards
```python
# GOOD: Clear, documented, error-handled
def load_document(self, file_path: str) -> Dict[str, Any]:
    """
    Load document via UNO API.
    
    Args:
        file_path: Absolute path to document
        
    Returns:
        Dict containing success status and document info
        
    Raises:
        FileNotFoundError: If document doesn't exist
        RuntimeError: If UNO connection fails
    """
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Document not found: {file_path}")
    
    try:
        # Implementation with proper error handling
        pass
    except Exception as e:
        logger.error(f"Failed to load document: {e}")
        raise

# BAD: No docs, no error handling, unclear
def load(self, path):
    doc = self.desktop.loadComponentFromURL(path, "_blank", 0, [])
    return doc
```

### 4. Implementation Guidelines

#### 4.1 Start Small, Build Incrementally
- Implement core functionality first
- Add features progressively
- Test at each step
- Don't try to build everything at once

#### 4.2 Platform Awareness
```python
# Always handle platform differences explicitly
if platform.system() == "Windows":
    # Windows-specific implementation
elif platform.system() == "Linux":
    # Linux-specific implementation
elif platform.system() == "Darwin":
    # macOS-specific implementation
else:
    raise NotImplementedError(f"Platform {platform.system()} not supported")
```

#### 4.3 Error Handling Philosophy
- **Fail fast** with clear error messages
- **Log everything** for debugging
- **Recover gracefully** when possible
- **Never silently ignore** errors

### 5. Documentation Standards

#### 5.1 Code Documentation
- Every class needs a docstring explaining its purpose
- Every method needs parameter and return documentation
- Complex logic needs inline comments
- Use type hints for clarity

#### 5.2 Progress Documentation
- Update TODO_CURRENT.md after each work session
- Document decisions in IMPLEMENTATION_PLAN.md
- Track completion in progress.md
- Note blockers and solutions

### 6. Testing Approach

#### 6.1 Test-Driven Thinking
Before implementing:
- Define success criteria
- Plan test cases
- Consider edge cases
- Think about error scenarios

#### 6.2 Incremental Testing
```python
# Test each component as you build
def test_uno_connection():
    """Verify UNO connection works before building on it"""
    conn = UNOConnection()
    assert conn.connect(), "Failed to establish UNO connection"
    
def test_document_loading():
    """Test document loading after connection works"""
    # Only test this after connection is verified
    pass
```

### 7. Communication Patterns

#### 7.1 Progress Updates
When asked to "ITERATE":
1. Read all planning documents
2. Assess current state
3. Report what's completed
4. Identify blockers
5. Propose next steps

#### 7.2 Problem Reporting
When encountering issues:
- Describe the specific problem
- Show relevant error messages
- Explain what was tried
- Suggest potential solutions

### 8. Performance Considerations

#### 8.1 Resource Management
```python
# Always clean up resources
class DocumentManager:
    def __enter__(self):
        self.connection = self.establish_connection()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup_resources()
```

#### 8.2 Optimization Strategy
- Make it work first
- Make it right second
- Make it fast third
- Profile before optimizing

### 9. Integration Best Practices

#### 9.1 Preserve Existing Functionality
- Never break working features
- Maintain backward compatibility
- Provide migration paths
- Document breaking changes

#### 9.2 Modular Integration
```python
# Good: Loosely coupled
class DocumentProcessor:
    def __init__(self, converter: IDocumentConverter):
        self.converter = converter  # Dependency injection
        
# Bad: Tightly coupled
class DocumentProcessor:
    def __init__(self):
        self.converter = LibreOfficeConverter()  # Hard-coded dependency
```

### 10. Debugging Philosophy

#### 10.1 Systematic Debugging
1. Reproduce the issue consistently
2. Isolate the component
3. Add detailed logging
4. Test hypothesis
5. Verify fix doesn't break other things

#### 10.2 Logging Strategy
```python
logger.debug("Entering method with params: %s", params)  # Detailed trace
logger.info("Processing document: %s", filename)         # Key operations
logger.warning("Retrying connection: attempt %d", count) # Potential issues
logger.error("Failed to load document: %s", error)      # Errors
```

## Research Protocol (TOOL Command)

### When "TOOL" is Called:

The model will search for best practices and expert recommendations using:

1. **Web Search Priority**
   ```
   Search queries:
   - "[Technology] best practices 2024"
   - "[Feature] implementation guide"
   - "[Problem] solution stackoverflow"
   - "[Library] documentation official"
   ```

2. **Research Sources** (in priority order):
   - **Official Documentation**: Library/framework official docs
   - **GitHub Repositories**: Popular implementations, examples
   - **Stack Overflow**: Specific problem solutions
   - **Research Articles**: Academic papers for algorithms
   - **Developer Blogs**: Expert insights and tutorials
   - **Slack/Discord Communities**: Real-world experiences

3. **Research Process**
   ```python
   def research_best_practices(feature):
       sources = []
       
       # 1. Official docs
       sources.append(search_official_docs(feature))
       
       # 2. GitHub examples
       sources.append(search_github_repos(
           query=f"{feature} implementation",
           sort="stars",
           language="python"
       ))
       
       # 3. Stack Overflow solutions
       sources.append(search_stackoverflow(
           query=f"{feature} best practices",
           tags=["python", "libreoffice", "uno-api"]
       ))
       
       # 4. Recent articles
       sources.append(search_articles(
           query=f"{feature} guide 2024",
           type="tutorial"
       ))
       
       return synthesize_recommendations(sources)
   ```

4. **Research Output Format**
   ```markdown
   ## Research Results: [Feature Name]
   
   ### Best Practices Found:
   1. **Source**: [Official Docs/GitHub/SO]
      - Recommendation: ...
      - Code Example: ...
      - Pros/Cons: ...
   
   ### Implementation Recommendations:
   - Preferred approach based on research
   - Common pitfalls to avoid
   - Performance considerations
   - Security implications
   
   ### Example Implementations:
   - Link to reference implementation
   - Code snippets from trusted sources
   ```

5. **Specific Research Areas**

   **For UNO/LibreOffice**:
   - Search: "LibreOffice UNO API python examples"
   - GitHub: openoffice/libreoffice repos
   - Forums: ask.libreoffice.org
   
   **For PyWebView**:
   - Official: pywebview.flowrl.com
   - GitHub: r0x0r/pywebview examples
   - Issues: Check closed issues for solutions
   
   **For Platform-Specific**:
   - Windows: Win32 API documentation
   - Linux: X11/XEmbed protocols
   - macOS: Cocoa/NSView documentation

### Example TOOL Usage:

```
User: "TOOL - research best practices for UNO document loading"

Model will:
1. Search official LibreOffice UNO documentation
2. Find GitHub repos with UNO implementations
3. Check Stack Overflow for common issues/solutions
4. Look for recent tutorials/guides
5. Synthesize findings into actionable recommendations
```

## Iteration Protocol

### When "ITERATE" is Called:

1. **Load Context**
   ```python
   documents = [
       "TODO_CURRENT.md",      # Current task status
       "IMPLEMENTATION_PLAN.md", # Overall strategy
       "progress.md",          # Implementation state
       "EXECUTION_PLAN_*.md"   # Current feature plan
   ]
   ```

2. **Analyze State**
   - What's implemented?
   - What's working?
   - What's blocking?
   - What's next?

3. **Update Status**
   - Mark completed items
   - Note new issues
   - Update timelines
   - Document decisions

4. **Plan Next Steps**
   - If blocked: Propose solutions
   - If complete: Move to next task
   - If partial: Continue current task

## Quality Checklist

Before considering any feature complete:

- [ ] Core functionality works
- [ ] Error handling implemented
- [ ] Platform differences handled
- [ ] Documentation updated
- [ ] Basic tests written
- [ ] Integration verified
- [ ] Performance acceptable
- [ ] No regressions introduced

## Key Reminders

1. **Read before writing** - Understand existing code
2. **Plan before coding** - Think through the approach
3. **Test as you go** - Verify each component
4. **Document everything** - Future you will thank you
5. **Handle errors gracefully** - Expect the unexpected
6. **Keep it modular** - Enable future changes
7. **Communicate clearly** - Explain decisions and blockers

## Success Metrics

Good implementation has:
- **Clear code** that's self-documenting
- **Robust error handling** for all scenarios
- **Comprehensive logging** for debugging
- **Modular design** for maintainability
- **Complete documentation** for understanding
- **Working tests** for confidence
- **Cross-platform support** for compatibility

---
**Purpose**: Define model behavior for maximum accuracy and efficiency in DocAI Native development
**Last Updated**: 2024-01-17
**Review**: Before each major implementation task