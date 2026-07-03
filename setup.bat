@echo off

:: Install Python dependencies
pip install -U -r requirements.txt

:: Install FFmpeg so that the bot can play audio
winget install "FFmpeg (Essentials Build)"

:: Create token.json if it doesn't exist
if not exist "token.json" (
    (
        echo {
        echo     "token": "PASTE_YOUR_BOT_TOKEN_HERE"
        echo }
    ) > token.json

    echo.
    echo Created token.json.
    echo Please open it and replace PASTE_YOUR_BOT_TOKEN_HERE with your Discord bot token.
    echo.
)

:: Setup is finished
echo Finished setup.
pause