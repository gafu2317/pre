# GEMINI.md

回答は日本語

## Project Overview

This project is a Python web application designed to analyze conversation logs and visualize their argumentative structure. It uses a Large Language Model (LLM) to parse the text and identify key components of the discussion based on established argumentation theories. The application is built with Streamlit, providing an interactive user interface for text input and graph visualization.

The core of the project lies in its ability to apply different analytical lenses or "strategies" to the text. Currently, it implements the **IBIS (Issue-Based Information System)** model, which is well-suited for capturing the structure of problem-solving and design-related discussions. The extracted structure is then rendered as a clear and easy-to-understand diagram using Mermaid.js.

The architecture is modular, using a strategy pattern to allow for easy extension with other argumentation models in the future (e.g., a placeholder for the Toulmin model already exists).

## Key Technologies

*   **Backend:** Python
*   **Web Framework:** Streamlit
*   **LLM Integration:** OpenAI API (`gpt-4o-mini`)
*   **Data Modeling:** Pydantic
*   **Visualization:** `streamlit-mermaid` for rendering Mermaid.js graphs
*   **Dependencies:** `openai`, `streamlit`, `pydantic`, `python-dotenv`, `streamlit-mermaid`

## Building and Running the Project

To run this application, follow these steps:

1.  **Set up the Environment:**
    Ensure you have Python 3.8+ installed. It is recommended to use a virtual environment.

2.  **Install Dependencies:**
    Install all the required Python packages from the `requirements.txt` file.

    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure API Key:**
    The application requires access to the OpenAI API. Create a `.env` file in the project's root directory and add your API key to it:

    ```
    # .env
    OPENAI_API_KEY="sk-..."
    ```
    The application will automatically load this key.

4.  **Run the Application:**
    Launch the Streamlit web server using the following command:

    ```bash
    streamlit run main.py
    ```
    This will start the application and open it in your default web browser.

## Development Conventions

*   **Modular Architecture:** The code is organized into modules within the `src/` directory.
    *   `main.py`: The main Streamlit application entry point and UI definition.
    *   `src/models.py`: Contains the Pydantic models (`ArgumentGraph`, `Node`, `Edge`) that define the core data structure.
    *   `src/strategies/`: Implements the analysis logic using a strategy pattern. `base.py` defines the interface, and other files (`ibis.py`, `toulmin.py`) provide concrete implementations.
    *   `src/llm.py`: A dedicated client for interacting with the OpenAI API. It is configured to request JSON output to ensure reliable data parsing.
    *   `src/visualizer.py`: A generator class that converts the `ArgumentGraph` Pydantic model into a Mermaid.js graph syntax string.

*   **Strategy Pattern:** To add a new analysis model, create a new class in the `src/strategies/` directory that inherits from `MiningStrategy` and implement the `analyze` method. Then, update `main.py` to include it as an option.

*   **Data Validation:** Pydantic models are used to enforce the structure of the data returned by the LLM, ensuring type safety and preventing errors during graph generation.

*   **State Management:** The Streamlit session state (`st.session_state`) is used to persist the generated graph data across user interactions, preventing re-analysis on every UI update.

ユークリッド距離かコサイン類似度を使って次元数を削減せずに色に変換する
HSVも使ってみる
実際のユークリッド距離やコサイン類似度を表示する
仮説として色の変化が話題の脱線とリンクしている
    話題がずれていないのに、色が変わりすぎていることは避けたい
