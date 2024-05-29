# Use the official Python image from the Docker Hub
FROM python:3.12

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set environment variables for PostgreSQL connection
ENV DATABASE_HOST=ep-shy-pine-a2e1ouuw.eu-central-1.pg.koyeb.app
ENV DATABASE_USER=koyeb-adm
ENV DATABASE_PASSWORD=WCAFr1R0muaZ
ENV DATABASE_NAME=koyebdb

# Expose the port (if necessary, though not needed for a Telegram bot)
EXPOSE 8080

# Run the bot
CMD ["python", "bot.py"]