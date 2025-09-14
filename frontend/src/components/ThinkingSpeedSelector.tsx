import { useState } from 'react';

interface ThinkingSpeedSelectorProps {
  onSpeedChange?: (speed: 'quick' | 'normal' | 'long') => void;
  currentSpeed?: 'quick' | 'normal' | 'long';
}

export default function ThinkingSpeedSelector({ onSpeedChange, currentSpeed = 'normal' }: ThinkingSpeedSelectorProps) {
  const [selectedSpeed, setSelectedSpeed] = useState<'quick' | 'normal' | 'long'>(currentSpeed);

  const handleSpeedChange = (speed: 'quick' | 'normal' | 'long') => {
    setSelectedSpeed(speed);
    if (onSpeedChange) {
      onSpeedChange(speed);
    }
  };

  const getSpeedDescription = (speed: string) => {
    switch (speed) {
      case 'quick':
        return 'Fast responses, less detailed analysis';
      case 'normal':
        return 'Balanced speed and detail';
      case 'long':
        return 'Thorough analysis, slower responses';
      default:
        return '';
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-600 shadow-sm">
      <div className="p-4 border-b border-gray-600 bg-gray-900 rounded-t-lg">
        <h3 className="text-sm font-semibold text-gray-100 flex items-center gap-2">
          <span className="text-gray-600">⚡</span>
          Thinking Speed
        </h3>
      </div>

      <div className="p-4 space-y-4">
        {/* Current Speed Display */}
        <div>
          <h4 className="text-xs font-medium text-gray-200 mb-2 uppercase tracking-wider">Current Speed</h4>
          <div className="form-input rounded-md p-2 text-center">
            <div className="text-xs">
              <div className="font-medium text-gray-100 capitalize">
                {selectedSpeed}
              </div>
              <div className="text-gray-400 text-xs mt-1">
                {getSpeedDescription(selectedSpeed)}
              </div>
            </div>
          </div>
        </div>

        {/* Speed Buttons */}
        <div>
          <div>
            <label className="block text-xs font-medium text-gray-200 mb-2">
              Select Speed
            </label>
            <div className="flex flex-col gap-2">
              <button
                onClick={() => handleSpeedChange('quick')}
                className={`w-full px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  selectedSpeed === 'quick'
                    ? 'bg-blue-600 hover:bg-blue-700 text-white focus:ring-2 focus:ring-blue-500 focus:ring-offset-1'
                    : 'bg-gray-700 hover:bg-gray-600 text-gray-200 focus:ring-2 focus:ring-gray-500 focus:ring-offset-1'
                }`}
              >
                Quick
              </button>

              <button
                onClick={() => handleSpeedChange('normal')}
                className={`w-full px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  selectedSpeed === 'normal'
                    ? 'bg-blue-600 hover:bg-blue-700 text-white focus:ring-2 focus:ring-blue-500 focus:ring-offset-1'
                    : 'bg-gray-700 hover:bg-gray-600 text-gray-200 focus:ring-2 focus:ring-gray-500 focus:ring-offset-1'
                }`}
              >
                Normal
              </button>

              <button
                onClick={() => handleSpeedChange('long')}
                className={`w-full px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  selectedSpeed === 'long'
                    ? 'bg-blue-600 hover:bg-blue-700 text-white focus:ring-2 focus:ring-blue-500 focus:ring-offset-1'
                    : 'bg-gray-700 hover:bg-gray-600 text-gray-200 focus:ring-2 focus:ring-gray-500 focus:ring-offset-1'
                }`}
              >
                Long
              </button>
            </div>
          </div>

          <p className="text-xs text-gray-500 leading-relaxed">
            Choose response speed. Affects processing time and detail level.
          </p>
        </div>
      </div>
    </div>
  );
}
