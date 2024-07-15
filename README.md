# Indirect Emissions Modeller
Estimate the greenhouse gas emissions from commuting and Working from Home (WFH) using a synthetic staff population. 

There are stochastic elements so the same settings are likely to produce different results, so a series of runs are recommended and taking a measure of central tendency.

## Installation
If running from your own computer:
1. Set a new virtual environment, e.g. using `conda create -n emissions_modeller python=3.11 numpy pandas=2.1.4 streamlit=1.36 PyYAML plotly`
2. Alternatively use `requirements.txt` to specify a new virtual environment.
3. Install the SDK of your choice
4. Clone the [repo](https://github.com/jverrall/emissions_model)

## Running the app
1. Open `app.py` in your SDK (VSCode is recommended by Streamlit) and run using the terminal command `streamlit run app.py` from the correct directory
2. Play with the settings to your heart's content
3. Click the **Download** button to export the main settings and emissions

## License
MIT