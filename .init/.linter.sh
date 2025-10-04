#!/bin/bash
cd /home/kavia/workspace/code-generation/codeassist-ai-4321-4330/backend_service
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

