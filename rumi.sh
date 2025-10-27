#!/bin/bash
# Ask Rumi - Short Commands for Server Management

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

case "$1" in
    start)
        echo -e "${GREEN}🚀 Starting Ask Rumi Backend...${NC}"
        # Kill any existing processes on port 8001
        lsof -ti:8001 | xargs kill -9 2>/dev/null
        sleep 1
        cd /Users/abdulbasit/Documents/AppsAI/askrumi/RumiBackend
        source venv/bin/activate
        uvicorn main:app --host 127.0.0.1 --port 8001 --reload
        ;;
    
    stop)
        echo -e "${RED}🛑 Stopping Ask Rumi Backend...${NC}"
        pkill -9 uvicorn
        echo -e "${GREEN}✅ Server stopped${NC}"
        ;;
    
    restart)
        echo -e "${YELLOW}🔄 Restarting Ask Rumi Backend...${NC}"
        pkill -9 uvicorn
        sleep 1
        cd /Users/abdulbasit/Documents/AppsAI/askrumi/RumiBackend
        source venv/bin/activate
        uvicorn main:app --host 127.0.0.1 --port 8001 --reload &
        echo -e "${GREEN}✅ Server restarted${NC}"
        ;;
    
    status)
        if pgrep -x uvicorn > /dev/null; then
            echo -e "${GREEN}✅ Server is running on http://127.0.0.1:8001${NC}"
            curl -s http://127.0.0.1:8001/ | python3 -m json.tool 2>/dev/null || echo "Server not responding"
        else
            echo -e "${RED}❌ Server is not running${NC}"
        fi
        ;;
    
    kill)
        echo -e "${RED}💀 Killing all uvicorn processes...${NC}"
        pkill -9 uvicorn
        echo -e "${GREEN}✅ All processes killed${NC}"
        ;;
    
    *)
        echo "Ask Rumi - Server Management"
        echo ""
        echo "Usage: ./rumi.sh [command]"
        echo ""
        echo "Commands:"
        echo "  start     - Start the server"
        echo "  stop      - Stop the server"
        echo "  restart   - Restart the server (kill + start)"
        echo "  kill      - Kill all uvicorn processes"
        echo "  status    - Check if server is running"
        echo ""
        echo "Examples:"
        echo "  ./rumi.sh start"
        echo "  ./rumi.sh stop"
        echo "  ./rumi.sh restart"
        ;;
esac

