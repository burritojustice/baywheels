# Bay Wheels Neighborhood Flows - Multi-Month Setup

## Overview

This refactored version separates **geometry** (which is static) from **data** (which changes monthly), allowing you to efficiently switch between different time periods without reloading the map geometries.

## File Structure

```
baywheels/
├── neighborhoods/
│   ├── index.html                          # Main map application
│   ├── neighborhoods.geojson               # Polygon geometries (names only)
│   ├── neighborhood_centroids.geojson      # Point geometries (names only)
│   └── baywheels_stations.geojson         # Station points
└── data/
    ├── 2024-10.json                        # October 2024 ride data
    ├── 2024-09.json                        # September 2024 ride data (future)
    └── 2024-08.json                        # August 2024 ride data (future)
```

## Data File Format

Each month's data file (`data/YYYY-MM.json`) should have this structure:

```json
{
  "month": "2024-10",
  "generated": "2024-11-18",
  "neighborhoods": {
    "South of Market": {
      "total_starts": 26319,
      "total_ends": 27064,
      "destinations": {
        "Financial District/South Beach": 5450,
        "Mission Bay": 3915,
        ...
      },
      "origins": {
        "Financial District/South Beach": 4978,
        "Mission": 3915,
        ...
      }
    },
    "Presidio": {
      "total_starts": 8107,
      "total_ends": 8287,
      "destinations": { ... },
      "origins": { ... }
    },
    ...
  }
}
```

### Required Fields Per Neighborhood:
- `total_starts` - Total rides starting in this neighborhood
- `total_ends` - Total rides ending in this neighborhood  
- `destinations` - Object mapping destination neighborhoods to ride counts (rides TO other neighborhoods)
- `origins` - Object mapping origin neighborhoods to ride counts (rides FROM other neighborhoods)

## Converting Your Current Data

If you have `neighborhood_centroids_with_od.geojson`, you can extract the data into the JSON format:

```python
import json

# Load your current geojson
with open('neighborhood_centroids_with_od.geojson', 'r') as f:
    geojson = json.load(f)

# Extract data
month_data = {
    "month": "2024-10",
    "generated": "2024-11-18",
    "neighborhoods": {}
}

for feature in geojson['features']:
    props = feature['properties']
    nhood = props['nhood']
    
    month_data['neighborhoods'][nhood] = {
        "total_starts": props.get('total_starts', 0),
        "total_ends": props.get('total_ends', 0),
        "destinations": props.get('destinations', {}),
        "origins": props.get('origins', {})
    }

# Save as JSON
with open('data/2024-10.json', 'w') as f:
    json.dump(month_data, f, indent=2)
```

## Adding New Months

1. **Create data file**: Add new JSON file to `data/` folder (e.g., `data/2024-09.json`)

2. **Update index.html**: Add the month to the `AVAILABLE_MONTHS` array:

```javascript
const AVAILABLE_MONTHS = [
  { id: '2024-10', label: 'October 2024', dataUrl: 'https://burritojustice.github.io/baywheels/data/2024-10.json' },
  { id: '2024-09', label: 'September 2024', dataUrl: 'https://burritojustice.github.io/baywheels/data/2024-09.json' },
  { id: '2024-08', label: 'August 2024', dataUrl: 'https://burritojustice.github.io/baywheels/data/2024-08.json' },
];
```

That's it! The dropdown and arrow buttons will automatically update.

## How It Works

### Initial Load:
1. Load geometry files (neighborhoods, centroids, stations) - **once**
2. Load data for current month
3. Use `setFeatureState()` to attach data to polygons
4. Render map with color-coded neighborhoods

### Switching Months:
1. Fetch new month's data file
2. Update feature-state for all neighborhoods with new data
3. Map automatically re-renders with new colors
4. If a neighborhood is selected, update the flow visualization

### Performance Benefits:
- ✅ Geometry files loaded only once (cached by browser)
- ✅ Data files are small (~50KB vs 500KB+ with embedded geometry)
- ✅ Fast month switching (no geometry re-upload)
- ✅ Smooth animations possible between months
- ✅ Easy to add new time periods

## UI Controls

- **Dropdown menu**: Select any available month
- **Left arrow (◄)**: Go to previous month (disabled on first month)
- **Right arrow (►)**: Go to next month (disabled on last month)
- **Loading indicator**: Shows when fetching data

## Keyboard Shortcuts (Optional Enhancement)

You can add keyboard shortcuts for month navigation:

```javascript
document.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowLeft' && currentMonthIndex > 0) {
    prevBtn.click();
  } else if (e.key === 'ArrowRight' && currentMonthIndex < AVAILABLE_MONTHS.length - 1) {
    nextBtn.click();
  }
});
```

## Future Enhancements

### Time Series Animation:
```javascript
let animating = false;
let animationInterval;

function startAnimation() {
  animating = true;
  animationInterval = setInterval(() => {
    if (currentMonthIndex < AVAILABLE_MONTHS.length - 1) {
      nextBtn.click();
    } else {
      stopAnimation();
    }
  }, 2000); // Change month every 2 seconds
}
```

### Compare Two Months:
- Load two data files
- Show difference in colors
- Highlight neighborhoods with biggest changes

### Aggregate Statistics:
- Total rides across all months
- Trend lines
- Seasonal patterns

## Notes

- The geometry files (`neighborhoods.geojson` and `neighborhood_centroids.geojson`) should only contain the `nhood` property and geometry
- All ride data lives in the monthly JSON files
- Feature-state is used to dynamically color polygons without modifying the source data
- This approach is recommended by MapLibre for frequently-changing data
