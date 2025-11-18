#!/usr/bin/env node

// Bikeshare JSON to GeoJSON Converter
// Usage: node convert.js input.json output.geojson

const fs = require('fs');
const path = require('path');

// Get command line arguments
const args = process.argv.slice(2);

if (args.length < 2) {
  console.error('Usage: node convert.js <input.json> <output.geojson>');
  console.error('Example: node convert.js bikeshare.json stations.geojson');
  process.exit(1);
}

const inputFile = args[0];
const outputFile = args[1];

// Check if input file exists
if (!fs.existsSync(inputFile)) {
  console.error(`Error: Input file '${inputFile}' not found`);
  process.exit(1);
}

// City name mapping based on short_name prefix
const cityMap = {
  'SJ': 'San Jose',
  'SF': 'San Francisco',
  'OK': 'Oakland',
  'BK': 'Berkeley',
  'DC': 'Daly City',
  'EM': 'Emeryville'
};

try {
  // Read and parse the JSON file
  console.log(`Reading ${inputFile}...`);
  const jsonData = JSON.parse(fs.readFileSync(inputFile, 'utf8'));
  
  // Convert to GeoJSON
  console.log('Converting to GeoJSON...');
  const geojson = {
    type: "FeatureCollection",
    features: jsonData.data.stations.map(station => {
      // Handle missing or undefined short_name
      const shortName = station.short_name || '';
      const prefix = shortName.length >= 2 ? shortName.substring(0, 2) : '';
      const city = cityMap[prefix] || 'Unknown';
      
      // Extract district (e.g., "SF-J30" -> "SF-J", "OK-AA3" -> "OK-AA", "SF-GGP-04" -> "SF-GGP")
      let district = null;
      if (shortName) {
        const dashIndex = shortName.indexOf('-');
        if (dashIndex !== -1) {
          // Get everything after the dash
          const afterDash = shortName.substring(dashIndex + 1);
          // Extract only the letters (remove numbers and additional dashes)
          const letters = afterDash.match(/^[A-Za-z]+/);
          if (letters) {
            district = shortName.substring(0, dashIndex + 1) + letters[0];
          }
        }
      }
      
      return {
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [station.lon, station.lat]
        },
        properties: {
          name: station.name,
          capacity: station.capacity,
          short_name: shortName,
          region_id: station.region_id,
          station_id: station.station_id,
          city: city,
          district: district,
          address: station.address || null
        }
      };
    })
  };
  
  // Write the GeoJSON file
  console.log(`Writing to ${outputFile}...`);
  fs.writeFileSync(outputFile, JSON.stringify(geojson, null, 2));
  
  console.log(`✓ Success! Converted ${geojson.features.length} stations`);
  
  // Show city breakdown
  const cityCounts = {};
  geojson.features.forEach(f => {
    const city = f.properties.city;
    cityCounts[city] = (cityCounts[city] || 0) + 1;
  });
  
  console.log('\nStations by city:');
  Object.entries(cityCounts)
    .sort((a, b) => b[1] - a[1])
    .forEach(([city, count]) => {
      console.log(`  ${city}: ${count} stations`);
    });
  
} catch (error) {
  console.error('Error:', error.message);
  process.exit(1);
}