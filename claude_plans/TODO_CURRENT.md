# Current TODO List - DocAI Native Implementation
**Last Updated**: July 23, 2025

## Active Task (IN PROGRESS)
- **Task**: LibreOffice Overlay Positioning (Phase 2 - Revised)
- **Priority**: HIGH
- **Status**: IMPLEMENTATION IN PROGRESS
- **Execution Plan**: `2025-07-24_OVERLAY_IMPLEMENTATION_PLAN.md`
- **Started**: July 24, 2025
- **Target Completion**: July 31, 2025 (1 week)
- **Approach**: Overlay positioning (NOT embedding)
- **Platform Focus**: Linux (X11) first, then Windows

## TODO List (Priority Order)

### High Priority
1. ✅ Document current implementation state and create progress.md
2. ✅ Create comprehensive implementation plan
3. ✅ **Enhance UNO Bridge with actual document loading via UNO API** (COMPLETED)
4. ✅ **Fix file loading and JavaScript integration** (COMPLETED Jan 22, 2025)
5. ✅ **Fix native file loading and port configuration** (COMPLETED July 23, 2025)
6. 🔄 **Implement LibreOffice overlay positioning system** (CURRENT - Phase 2 Revised)
   - ✅ All embedding tests completed - all failed
   - ✅ Research and planning complete
   - 🔄 Implementing overlay positioning approach
7. ⏳ Implement enhanced text extraction for AI via UNO
8. ⏳ Complete overlay window management
9. ⏳ Port RAG implementation from original DocAI
10. ⏳ Port AI providers and complete chat integration

### Implementation Checklist (Current Task)
- [x] Create implementation plan
- [ ] Create overlay directory structure
- [ ] Implement coordinate system
- [ ] Implement window tracker
- [ ] Implement decoration remover
- [ ] Implement sync engine
- [ ] Create overlay manager
- [ ] Integrate with PyWebView
- [ ] Add UI controls
- [ ] Test and validate

### Medium Priority
10. ⏳ Update frontend to use new API endpoints
11. ⏳ Implement native-only document viewing UI
12. ⏳ Create platform-specific embedding tests

### Low Priority
13. ⏳ Build system and create installers

## Status Legend
- ✅ Completed
- 🔄 In Progress
- ⏳ Pending
- ❌ Blocked

## Iteration Protocol

When you say "ITERATE", I will:

1. **Read all planning documents**:
   - `CLAUDE.md` - Original requirements
   - `IMPLEMENTATION_PLAN.md` - Overall implementation strategy
   - `progress.md` - Current state and gaps
   - `TODO_CURRENT.md` - This file with current tasks
   - `EXECUTION_PLAN_*.md` - Detailed plans for specific features

2. **Analyze current state**:
   - Check what's been completed
   - Identify any new issues or changes
   - Update status of current task

3. **Update documentation**:
   - Mark completed items
   - Update progress percentages
   - Note any deviations from plan

4. **Provide next action plan**:
   - If current task complete → Move to next TODO
   - If current task incomplete → Continue with specific next steps
   - Create new EXECUTION_PLAN_*.md for next feature if needed

## Completion Criteria for Current Task

The current task "Native LibreOffice Window Embedding" will be considered COMPLETE when:

- [ ] X11 window embedding works on Linux
- [ ] LibreOffice appears inside chat-container div
- [ ] Window resizing handled properly
- [ ] Text selection extraction implemented
- [ ] Win32 embedding works on Windows (or documented fallback)
- [ ] Frontend controls (fullscreen, close) working
- [ ] Fallback to HTML conversion when embedding fails
- [ ] Documentation and tests updated

## Notes
- Each task should have a detailed execution plan before starting
- Update this file immediately when task status changes
- Keep track of any blockers or dependencies
- Document lessons learned for future tasks

## Recent Achievements (2025)

### January 21, 2025
- ✅ Fixed LibreOffice UNO service process management
- ✅ Implemented HTML conversion with embedded images
- ✅ Backend integration successful

### January 22, 2025  
- ✅ Resolved PyWebView JavaScript execution order issues
- ✅ Fixed localStorage compatibility problems
- ✅ Implemented debug panel for troubleshooting

### July 23, 2025
- ✅ Fixed Flask port configuration (now using 8090)
- ✅ Added parent Documents directory to file search
- ✅ System-wide file picker fully functional
- ✅ Created comprehensive documentation

---
**Last Updated**: July 23, 2025
**Next Review**: Upon completion of Phase 2 or when "ITERATE" is called