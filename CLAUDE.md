# Claude Code Instructions

## Working Guidelines

1. **Think First, Read Code**: Always think through the problem first and read the codebase for relevant files before making changes.

2. **Check Before Major Changes**: Before making any major changes, check in with the user to verify the plan.

3. **High-Level Explanations**: Every step of the way, provide a high-level explanation of what changes were made.

4. **Simplicity First**: Make every task and code change as simple as possible. Avoid massive or complex changes. Every change should impact as little code as possible. Everything is about simplicity.

5. **Maintain Documentation**: Keep a documentation file that describes how the architecture of the app works inside and out.

6. **No Speculation**: Never speculate about code you have not opened. If the user references a specific file, read it first before answering. Investigate and read relevant files BEFORE answering questions about the codebase. Never make claims about code before investigating - give grounded and hallucination-free answers.

7. **Your context windows**: Your context window will be automatically compacted as it approaches its limit, allowing you to continue working indefinitely from where you left off. Therefore, do not stop tasks early due to token budget concerns. As you approach your token budget limit, save your current progress and state to memory before the context window refreshes. Always be as persistent and autonomous as possible and complete tasks fully, even if the end of your budget is approaching. Never artificially stop any task early regardless of the context remaining.

8. **Update files**: After every changes, update the files in folder @Dev to keep track of progress.

9. **Session Type First**: At the beginning of each session, determine the type of work to be done and create appropriate branch:
   - **Feature** (new functionality) → branch `feature/nazwa`
   - **Fix** (bug fix) → branch `fix/nazwa`
   - **Refactor** (refactoring) → branch `refactor/nazwa`
   - **Experiment** (experiment) → branch `exp/nazwa`
   - **Minor** (small changes) → directly on `main`