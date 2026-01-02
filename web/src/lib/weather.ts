// Weather service using Open-Meteo API (free, no API key required)

export interface WeatherData {
  temperature: number; // Fahrenheit
  apparentTemperature: number;
  humidity: number;
  windSpeed: number; // mph
  windDirection: number;
  weatherCode: number;
  precipitation: number;
  conditions: string;
  icon: string;
}

export interface ForecastDay {
  date: string;
  tempMax: number;
  tempMin: number;
  weatherCode: number;
  conditions: string;
  icon: string;
  precipProbability: number;
}

// Weather code to description mapping
const weatherCodes: Record<number, { description: string; icon: string }> = {
  0: { description: 'Clear sky', icon: '☀️' },
  1: { description: 'Mainly clear', icon: '🌤️' },
  2: { description: 'Partly cloudy', icon: '⛅' },
  3: { description: 'Overcast', icon: '☁️' },
  45: { description: 'Foggy', icon: '🌫️' },
  48: { description: 'Rime fog', icon: '🌫️' },
  51: { description: 'Light drizzle', icon: '🌧️' },
  53: { description: 'Moderate drizzle', icon: '🌧️' },
  55: { description: 'Dense drizzle', icon: '🌧️' },
  61: { description: 'Slight rain', icon: '🌧️' },
  63: { description: 'Moderate rain', icon: '🌧️' },
  65: { description: 'Heavy rain', icon: '🌧️' },
  66: { description: 'Freezing rain', icon: '🌨️' },
  67: { description: 'Heavy freezing rain', icon: '🌨️' },
  71: { description: 'Slight snow', icon: '🌨️' },
  73: { description: 'Moderate snow', icon: '🌨️' },
  75: { description: 'Heavy snow', icon: '❄️' },
  77: { description: 'Snow grains', icon: '❄️' },
  80: { description: 'Slight showers', icon: '🌦️' },
  81: { description: 'Moderate showers', icon: '🌦️' },
  82: { description: 'Violent showers', icon: '⛈️' },
  85: { description: 'Slight snow showers', icon: '🌨️' },
  86: { description: 'Heavy snow showers', icon: '❄️' },
  95: { description: 'Thunderstorm', icon: '⛈️' },
  96: { description: 'Thunderstorm with hail', icon: '⛈️' },
  99: { description: 'Thunderstorm with heavy hail', icon: '⛈️' },
};

function getWeatherInfo(code: number): { description: string; icon: string } {
  return weatherCodes[code] || { description: 'Unknown', icon: '❓' };
}

export async function getWeather(latitude: number, longitude: number): Promise<WeatherData | null> {
  try {
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch&timezone=America/Denver`;

    const response = await fetch(url);
    if (!response.ok) return null;

    const data = await response.json();
    const current = data.current;
    const weatherInfo = getWeatherInfo(current.weather_code);

    return {
      temperature: Math.round(current.temperature_2m),
      apparentTemperature: Math.round(current.apparent_temperature),
      humidity: current.relative_humidity_2m,
      windSpeed: Math.round(current.wind_speed_10m),
      windDirection: current.wind_direction_10m,
      weatherCode: current.weather_code,
      precipitation: current.precipitation,
      conditions: weatherInfo.description,
      icon: weatherInfo.icon,
    };
  } catch (error) {
    console.error('Failed to fetch weather:', error);
    return null;
  }
}

export async function getForecast(latitude: number, longitude: number): Promise<ForecastDay[] | null> {
  try {
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&temperature_unit=fahrenheit&timezone=America/Denver&forecast_days=7`;

    const response = await fetch(url);
    if (!response.ok) return null;

    const data = await response.json();
    const daily = data.daily;

    return daily.time.map((date: string, i: number) => {
      const weatherInfo = getWeatherInfo(daily.weather_code[i]);
      return {
        date,
        tempMax: Math.round(daily.temperature_2m_max[i]),
        tempMin: Math.round(daily.temperature_2m_min[i]),
        weatherCode: daily.weather_code[i],
        conditions: weatherInfo.description,
        icon: weatherInfo.icon,
        precipProbability: daily.precipitation_probability_max[i],
      };
    });
  } catch (error) {
    console.error('Failed to fetch forecast:', error);
    return null;
  }
}

// Get climbing recommendation based on weather
export function getClimbingRecommendation(weather: WeatherData): {
  recommendation: 'excellent' | 'good' | 'caution' | 'dangerous';
  message: string;
} {
  const { temperature, windSpeed, weatherCode, precipitation } = weather;

  // Dangerous conditions
  if (weatherCode >= 95 || windSpeed > 40 || precipitation > 0.5) {
    return {
      recommendation: 'dangerous',
      message: 'Not recommended for climbing. Severe weather conditions.',
    };
  }

  // Caution conditions
  if (weatherCode >= 61 || windSpeed > 25 || temperature < 20 || temperature > 90) {
    return {
      recommendation: 'caution',
      message: 'Exercise caution. Check conditions before climbing.',
    };
  }

  // Good conditions
  if (weatherCode <= 2 && windSpeed < 15 && temperature >= 40 && temperature <= 75) {
    return {
      recommendation: 'excellent',
      message: 'Excellent conditions for climbing!',
    };
  }

  return {
    recommendation: 'good',
    message: 'Good conditions for climbing.',
  };
}
