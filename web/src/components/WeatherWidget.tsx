'use client';

import { useEffect, useState } from 'react';
import { getWeather, getForecast, getClimbingRecommendation, WeatherData, ForecastDay } from '@/lib/weather';
import { cn } from '@/lib/utils';

interface WeatherWidgetProps {
  latitude: number;
  longitude: number;
  peakName: string;
}

export function WeatherWidget({ latitude, longitude, peakName }: WeatherWidgetProps) {
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [forecast, setForecast] = useState<ForecastDay[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    async function fetchWeather() {
      setLoading(true);
      setError(false);

      try {
        const [weatherData, forecastData] = await Promise.all([
          getWeather(latitude, longitude),
          getForecast(latitude, longitude),
        ]);

        setWeather(weatherData);
        setForecast(forecastData);
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    }

    fetchWeather();
  }, [latitude, longitude]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Weather Conditions</h2>
        <div className="animate-pulse space-y-3">
          <div className="h-16 bg-gray-200 rounded"></div>
          <div className="h-8 bg-gray-200 rounded w-3/4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error || !weather) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Weather Conditions</h2>
        <p className="text-gray-500 text-sm">Unable to load weather data. Please try again later.</p>
      </div>
    );
  }

  const recommendation = getClimbingRecommendation(weather);

  const recommendationColors = {
    excellent: 'bg-green-100 border-green-300 text-green-800',
    good: 'bg-blue-100 border-blue-300 text-blue-800',
    caution: 'bg-yellow-100 border-yellow-300 text-yellow-800',
    dangerous: 'bg-red-100 border-red-300 text-red-800',
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr + 'T00:00:00');
    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Weather at {peakName}</h2>

      {/* Current conditions */}
      <div className="flex items-center gap-4 mb-4">
        <div className="text-5xl">{weather.icon}</div>
        <div>
          <div className="text-3xl font-bold text-gray-900">{weather.temperature}°F</div>
          <div className="text-sm text-gray-600">{weather.conditions}</div>
        </div>
      </div>

      {/* Weather details */}
      <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
        <div className="flex items-center gap-2 text-gray-600">
          <span>🌡️</span>
          <span>Feels like {weather.apparentTemperature}°F</span>
        </div>
        <div className="flex items-center gap-2 text-gray-600">
          <span>💧</span>
          <span>Humidity {weather.humidity}%</span>
        </div>
        <div className="flex items-center gap-2 text-gray-600">
          <span>💨</span>
          <span>Wind {weather.windSpeed} mph</span>
        </div>
        <div className="flex items-center gap-2 text-gray-600">
          <span>🌧️</span>
          <span>Precip {weather.precipitation}&quot;</span>
        </div>
      </div>

      {/* Climbing recommendation */}
      <div className={cn(
        'rounded-lg border p-3 mb-4',
        recommendationColors[recommendation.recommendation]
      )}>
        <div className="font-medium capitalize">{recommendation.recommendation} Conditions</div>
        <div className="text-sm opacity-90">{recommendation.message}</div>
      </div>

      {/* 7-day forecast */}
      {forecast && forecast.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">7-Day Forecast</h3>
          <div className="space-y-2">
            {forecast.slice(0, 5).map((day) => (
              <div key={day.date} className="flex items-center justify-between text-sm py-1 border-b border-gray-100 last:border-0">
                <span className="text-gray-600 w-24">{formatDate(day.date)}</span>
                <span className="text-lg">{day.icon}</span>
                <span className="text-gray-900 font-medium w-20 text-right">
                  {day.tempMax}° / {day.tempMin}°
                </span>
                <span className="text-gray-500 w-12 text-right">
                  {day.precipProbability}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <p className="text-xs text-gray-400 mt-4">
        Data from Open-Meteo. Updated every hour.
      </p>
    </div>
  );
}
