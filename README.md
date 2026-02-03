# sustainability-framework

## Setup

1. **Clone the repository:**

   ```sh
   git clone https://github.com/ZachVGonzales/sustainability-framework.git
   cd sustainability-framework
   ```

2. **Install Python dependencies:**

   ```sh
   uv sync
   ```

3. **Run Python commands inside uv's environment:**

   ```sh
   uv run main.py
   ```

> This project uses [uv](https://github.com/oven-sh/uv) for Python dependency management. Make sure you have `python3` and `uv` installed.

## Addings Apps

To add new apps to the sustainability framework, follow these steps:

1. **Create a new directory for the app:**

   Inside the `apps` directory, create a new folder named after your app (e.g., `my_app`).

   ```sh
   mkdir apps/my_app
   ```

2. **Add your app's code:**

   Place your app's files inside the newly created directory.
