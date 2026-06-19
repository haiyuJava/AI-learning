param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (Test-Path $python) {
    & $python -m personal_psych_assistant.knowledge @Arguments
} else {
    python -m personal_psych_assistant.knowledge @Arguments
}
