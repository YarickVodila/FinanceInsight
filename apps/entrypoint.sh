#!/bin/sh
cleanup() {
    echo "Завершение работы..."
    kill $FASTAPI_PID
    kill $BOT_PID
    exit 0
}
trap 'cleanup' SIGINT
python apps/api.py &
FASTAPI_PID=$!
python apps/bot.py &
BOT_PID=$!
wait $FASTAPI_PID
wait $BOT_PID
