# Calenbot - Discord Bot for Reservation Management

Calenbot is a Python-based Discord bot designed to manage reservations for various places and user schedules within a Discord server. The bot allows users to create and manage calendars, make reservations, and dynamically assign roles for command access.

## Features

- **Create and Manage Places**: Users can create and delete calendars for different places.
- **Reservations**: Users can make, view, and delete reservations, with validations to prevent overlapping bookings.
- **Role-Based Access**: Dynamically assign roles to specific commands, ensuring only authorized users can execute certain commands.
- **User-Friendly Interaction**: Clear and friendly prompts and error messages, with support for multiple date and time formats.
- **Automatic Monthly Reset**: Clears reservations at the beginning of each month to keep the calendar up-to-date.

## Commands

### Place Management
- `/create_place place_name`: Create a new place calendar.
- `/delete_place place_name`: Delete an existing place calendar.
- `/list_places`: List all available places.

### Reservation Management
- `/reserve place_name`: Reserve a time slot on a place calendar.
- `/delete_reservation place_name date time_from`: Delete an existing reservation.
- `/show_reservations place_name`: Show all reservations for a place calendar.

### Role Management
- `/assign_role command_name role`: Assign a role to a command.
- `/remove_role command_name role`: Remove a role from a command.

### Database Management
- `/clear_database`: Clear the entire database (with confirmation).

## Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/calenbot.git
   cd calenbot
   ```

2. **Set Up the Environment**:
   - Install required libraries:
     ```bash
     pip install discord.py python-dateutil python-dotenv
     ```
   - Create a `.env` file and add your bot token:
     ```ini
     DISCORD_BOT_TOKEN=your-bot-token
     ```

3. **Run the Bot**:
   ```bash
   python bot.py
   ```

## Assigning Roles to Commands

To assign a role to a command, use the `/assign_role` command. For example, to assign the "Admin" role to the `/delete_place` command, use:

```
/assign_role command_name:delete_place role:@Admin
```

This ensures that only users with the "Admin" role can execute the `/delete_place` command.

## Contributions

Contributions are welcome! Please fork the repository and create a pull request with your changes. Ensure that your code follows best practices and is well-documented.

## License

This project is licensed under the MIT License.

```

### Explanation

- **Project Title and Description**: The title and a brief description of what the bot does.
- **Features**: A list of key features provided by the bot.
- **Commands**: Detailed list of commands available and their descriptions.
- **Setup Instructions**: Step-by-step guide to set up the bot locally.
- **Assigning Roles to Commands**: Instructions on how to use the `/assign_role` command to restrict command access based on roles.
- **Contributions**: Invitation for contributions with guidelines.
- **License**: Information about the project's license.
