import React, { useEffect, useState } from 'react';
import { FaSun, FaMoon } from "react-icons/fa6";

const DarkModeToggle = () => {
  const [isDark, setIsDark] = useState(false);

  // On mount, check for a saved theme or system preference
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initialDark = savedTheme ? savedTheme === 'dark' : prefersDark;
    
    setIsDark(initialDark);
    document.documentElement.classList.toggle('dark', initialDark);
  }, []);

  const toggleDarkMode = () => {
    const newDarkMode = !isDark;
    setIsDark(newDarkMode);
    document.documentElement.classList.toggle('dark', newDarkMode);
    localStorage.setItem('theme', newDarkMode ? 'dark' : 'light');
  };

  return (
    <button
      onClick={toggleDarkMode}
      className="flex justify-center items-center w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700 focus:outline-none transition-colors duration-300"
      >
      {isDark ? (
        <span className="inline-block">
        <FaMoon />
        </span>
      ) : (
        <span className="inline-block">
        <FaSun />
        </span>
      )}
    </button>
  );
};

export default DarkModeToggle;
