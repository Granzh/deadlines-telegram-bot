# Deadlines Telegram Bot

Проект в стадии тестирования

Telegram bot for deadlines with notifications and timezones support.

## Features

- **Deadlines management**: Add, edit and delete your deadlines
- **Smart notifications**: Customizable reminders for 1 hour, 3 hours, 1 day,
  3 days or 1 week
- **Timezones**: Support all timezones for correct time display
- **Intuitive interface**: Simple commands with clear format
- **Single notifications**: Each reminder is sent only once
- **Deadline statuses**: Visual representation of task urgency

## Start

### Requirements

- Python 3.13+
- Telegram Bot Token
- SQLite (Default)

### Installation

1. **Clone repository**

   ```bash
   git clone https://github.com/Granzh/deadlines-telegram-bot
   cd deadlines-telegram-bot
   ```

2. **Setup environment**

   ```bash
   uv sync
   
   cp .env.development.example .env.development
   # or
   cp .env.production.example .env.production
   ```

3. **Bot settings**
Edit the `.env.development` file for development:  

    ```env
    # Development configuration
    BOT_TOKEN=
    DATABASE_URL=sqlite+aiosqlite:///./deadlines_dev.sqlite
    SCHEDULER_TIMEZONE=UTC
    LOG_LEVEL=DEBUG
    ENVIRONMENT=development
    DEBUG=true

    # Rate limiting (relaxed for development)
    RATE_LIMIT_TIME_WINDOW=10
    RATE_LIMIT_MAX_CALLS=20

    # Notifications (more frequent for testing)
    NOTIFICATION_CHECK_INTERVAL=1
    UPCOMING_CHECK_INTERVAL=1
    DEFAULT_NOTIFICATION_ENABLED=true
    DEFAULT_NOTIFICATION_ADVANCE_HOURS=24
    MAX_NOTIFICATION_ADVANCE_HOURS=168

    # Security (higher limits for development)
    MAX_TITLE_LENGTH=200
    MAX_DESCRIPTION_LENGTH=1000
    MAX_DEADLINE_TITLE_LENGTH=200
    MAX_DEADLINE_DESCRIPTION_LENGTH=1000
    MAX_DEADLINE_DESCRIPTION_LENGTH=1000
    ```

    Edit the `.env.production` file for production:

    ```env
    # Production configuration
    BOT_TOKEN=
    DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/deadlines_prod
    SCHEDULER_TIMEZONE=UTC
    LOG_LEVEL=WARNING
    ENVIRONMENT=production
    DEBUG=false

    # Rate limiting (stricter for production)
    RATE_LIMIT_TIME_WINDOW=60
    RATE_LIMIT_MAX_CALLS=10

    # Notifications
    NOTIFICATION_CHECK_INTERVAL=5
    UPCOMING_CHECK_INTERVAL=5
    DEFAULT_NOTIFICATION_ENABLED=true
    DEFAULT_NOTIFICATION_ADVANCE_HOURS=24
    MAX_NOTIFICATION_ADVANCE_HOURS=168

    # Security
    MAX_TITLE_LENGTH=100
    MAX_DESCRIPTION_LENGTH=500
    MAX_DEADLINE_TITLE_LENGTH=100
    MAX_DEADLINE_DESCRIPTION_LENGTH=500
    ```

4. **Apply database migrations**

   ```bash
   uv run alembic upgrade head
   ```

5. **Start**

   ```bash
   uv run python main.py
   ```

## Bot commands

| Command | Description |
| --------- | ---------- |
| `/start` | Start the bot |
| `/help` | List all available commands |
| `/add` | Add a new deadline |
| `/list` | Show all your deadlines |
| `/edit` | Edit an existing deadline |
| `/delete` | Delete a deadline |
| `/notifications` | Configure notification settings |
| `/change_timezone YOUR_TIMEZONE` | Change timezone |

## Docker deployment

### Running with Docker Compose

1. **Build and start**

   ```bash
   docker-compose up -d
   ```

2. **Migrations**

   ```bash
   docker-compose --profile migrations up migrations
   ```

### Health monitoring

The bot includes HTTP health monitoring for production deployment:

- **HTTP endpoint**: `GET /health` - JSON response for monitoring systems  
- **Health checks**: Database connectivity, scheduler status, memory usage
- **Graceful shutdown**: Proper cleanup on termination

Health check example response:

```json
{
  "status": "healthy",
  "uptime": "2h 15m 30s", 
  "timestamp": "2026-01-06T12:00:00.000Z",
  "services": {
    "database": {"status": "healthy"},
    "scheduler": {"status": "healthy", "jobs_count": 2},
    "memory": {"status": "healthy", "rss_mb": 140.5}
  }
}
```

### Environment variables

- `BOT_TOKEN` - Your Telegram bot token
- `DATABASE_URL` - database URL (SQLite by default)
- `SCHEDULER_TIMEZONE` - Timezone for scheduling (UTC)
- `LOG_LEVEL` - Logging level (INFO, DEBUG, ERROR)

## Testing

To run tests, use:

```bash
# Run all tests
uv run run_tests.py

# Run pytest with covarage 
uv run pytest --cov=.

# Run specific test file
uv run pytest tests/test_deadline_service.py
```

## Project structure

```markdown
deadlines-telegram-bot/
├── db/                     # Database models and sessions
├── handlers/               # Command handlers
├── services/               # Business logic
├── middleware/             # Middleware for request processing
├── utils/                  # Utilities and helper functions
├── migrations/             # Database migrations
├── tests/                  # Tests
├── docker-compose.yml      # Docker configuration
├── Dockerfile             # Docker image
└── alembic.ini            # Alembic configuration
```

**Enjoy using it!**
