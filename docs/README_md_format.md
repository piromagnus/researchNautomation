# Markdown Format Module Documentation

## Overview
The `md_format.py` module provides functions to format Markdown reports with ASCII visualizations, including histograms and scatter plots for paper score distributions and other data analysis.

## Architecture

### Core Components
- **ASCII Visualization**: Creates text-based charts and graphs
- **Data Analysis**: Processes numerical data for visualization
- **Markdown Formatting**: Generates properly formatted markdown output
- **Statistical Utilities**: Computes distributions and summaries

### Data Flow
```
Numerical Data → Statistical Analysis → ASCII Visualization → Markdown Formatting
```

## Function Signatures

### `create_ascii_histogram(data, bins=10, width=50) -> str`
**Purpose**: Creates an ASCII histogram representation of data
**Parameters**:
- `data` (list): Numerical data to visualize
- `bins` (int): Number of histogram bins (default: 10)
- `width` (int): Width of the histogram in characters (default: 50)

**Returns**: String containing ASCII histogram

### `create_ascii_scatter_plot(x_data, y_data, width=50, height=20) -> str`
**Purpose**: Creates an ASCII scatter plot
**Parameters**:
- `x_data` (list): X-axis values
- `y_data` (list): Y-axis values
- `width` (int): Plot width in characters (default: 50)
- `height` (int): Plot height in characters (default: 20)

**Returns**: String containing ASCII scatter plot

### `format_score_distribution(scores, title="Score Distribution") -> str`
**Purpose**: Formats score distribution with statistics and visualization
**Parameters**:
- `scores` (list): List of numerical scores
- `title` (str): Title for the distribution report

**Returns**: Formatted markdown with statistics and histogram

### `generate_summary_statistics(data) -> dict`
**Purpose**: Computes summary statistics for numerical data
**Parameters**:
- `data` (list): Numerical data to analyze

**Returns**: Dictionary with mean, median, std, min, max, quartiles

## Visualization Features

### ASCII Histogram
- Configurable bin count
- Proportional bar lengths
- Value labels and counts
- Statistical annotations

### ASCII Scatter Plot
- Character-based point plotting
- Axis labels and scales
- Correlation indicators
- Trend visualization

### Statistical Summary
- Descriptive statistics
- Distribution parameters
- Quartile analysis
- Outlier detection

## Usage Examples

### Basic Histogram
```python
import md_format as mdf

scores = [0.7, 0.8, 0.9, 0.6, 0.85, 0.75, 0.95]
histogram = mdf.create_ascii_histogram(scores)
print(histogram)
```

### Score Distribution Report
```python
formatted_report = mdf.format_score_distribution(
    scores, 
    title="Paper Relevance Scores"
)
```

### Scatter Plot Example
```python
x_values = [1, 2, 3, 4, 5]
y_values = [0.7, 0.8, 0.9, 0.85, 0.95]
scatter = mdf.create_ascii_scatter_plot(x_values, y_values)
```

## Output Format

### Histogram Output
```
Score Distribution
==================

Statistics:
- Mean: 0.79
- Median: 0.80
- Std Dev: 0.11
- Min: 0.60, Max: 0.95

Histogram:
0.60-0.67: ████ (1)
0.67-0.74: ████ (1)
0.74-0.81: ████████ (2)
0.81-0.88: ████████ (2)
0.88-0.95: ████ (1)
```

### Scatter Plot Output
```
Y
^
|  *
|    *
|      *
|    *
|  *
+--------> X
```

### Statistical Summary
```json
{
  "mean": 0.79,
  "median": 0.80,
  "std": 0.11,
  "min": 0.60,
  "max": 0.95,
  "q1": 0.725,
  "q3": 0.875,
  "count": 7
}
```

## Integration with Other Modules

### ArXiv Scraper Integration
- Visualizes relevance score distributions
- Plots paper count over time
- Shows threshold effectiveness

### Summary Module Integration
- Displays paper quality metrics
- Visualizes processing statistics
- Shows batch processing results

### Newsletter Generation
- Embeds visualizations in reports
- Creates data-driven insights
- Provides analytical summaries

## Configuration Options

### Histogram Settings
- `bins`: Number of histogram bins
- `width`: Character width of bars
- `show_stats`: Include statistical summary
- `normalize`: Show percentages vs counts

### Scatter Plot Settings
- `width`: Plot width in characters
- `height`: Plot height in characters
- `point_char`: Character for data points
- `axis_labels`: Custom axis labels

## Dependencies
- `numpy`: Numerical computations
- `statistics`: Built-in statistical functions
- Standard library only (no external visualization dependencies)

## Performance Characteristics
- **Memory Efficient**: ASCII-based, no graphics libraries
- **Fast Rendering**: Text-based output generation
- **Portable**: Works in any text environment
- **Lightweight**: Minimal dependencies

## Error Handling
- **Empty Data**: Handles empty datasets gracefully
- **Invalid Input**: Validates numerical data types
- **Overflow Protection**: Handles large datasets
- **Format Validation**: Ensures proper markdown output

## Use Cases
- Research report generation
- Data analysis documentation
- Terminal-based visualization
- Batch processing summaries
- Newsletter statistics
- Academic paper analysis