import { useState } from 'react';
import { 
  FiBook, 
  FiFileText, 
  FiSun, 
  FiMoon, 
  FiUser,
  FiSettings,
  FiLogOut,
  FiChevronDown 
} from 'react-icons/fi';

const Navbar = () => {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <nav className="bg-black border-b border-gray-800 px-4 py-2 flex items-center justify-between sticky top-0 z-50">
      {/* Left: Brand */}
      <div className="flex items-center space-x-2">
        <img 
          src="/logo.png" 
          alt="DataCue Logo" 
          className="w-8 h-8 object-contain"
        />
        <div>
          <h1 className="text-lg font-bold text-white">
            DataCue
          </h1>
        </div>
      </div>

      {/* Center: Menu Items */}
      <div className="hidden md:flex items-center space-x-1">
        <a 
          href="/docs" 
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-white text-sm hover:bg-gray-900 transition-all duration-200"
        >
          <FiBook className="text-base" />
          <span>Docs</span>
        </a>
        <a 
          href="/logs" 
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-white text-sm hover:bg-gray-900 transition-all duration-200"
        >
          <FiFileText className="text-base" />
          <span>Logs</span>
        </a>
      </div>

      {/* Right: Theme + Profile */}
      <div className="flex items-center space-x-2">
        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:bg-gray-900 transition-all duration-200"
          aria-label="Toggle theme"
        >
          {isDarkMode ? (
            <FiSun className="text-lg text-yellow-400" />
          ) : (
            <FiMoon className="text-lg text-white" />
          )}
        </button>

        {/* Profile Dropdown */}
        <div className="relative">
          <button
            onClick={() => setIsProfileOpen(!isProfileOpen)}
            className="flex items-center space-x-1.5 hover:bg-gray-900 px-2 py-1.5 rounded-lg transition-all duration-200"
          >
            <div className="w-7 h-7 bg-gray-700 rounded-full flex items-center justify-center">
              <FiUser className="text-white text-base" />
            </div>
            <div className="hidden sm:block text-left">
              <p className="text-xs font-semibold text-white">User</p>
            </div>
            <FiChevronDown className={`text-gray-400 text-sm transition-transform duration-200 ${isProfileOpen ? 'rotate-180' : ''}`} />
          </button>

          {/* Dropdown Menu */}
          {isProfileOpen && (
            <div className="absolute right-0 mt-2 w-56 bg-gray-900 rounded-xl shadow-xl border border-gray-800 py-2 animate-fadeIn">
              <div className="px-4 py-3 border-b border-gray-800">
                <p className="text-sm font-semibold text-white">User Account</p>
                <p className="text-xs text-gray-400 mt-1">user@datacue.ai</p>
              </div>
              <a
                href="/profile"
                className="flex items-center space-x-3 px-4 py-2.5 hover:bg-gray-800 transition-colors"
              >
                <FiUser className="text-gray-400" />
                <span className="text-sm text-white">Profile</span>
              </a>
              <a
                href="/settings"
                className="flex items-center space-x-3 px-4 py-2.5 hover:bg-gray-800 transition-colors"
              >
                <FiSettings className="text-gray-400" />
                <span className="text-sm text-white">Settings</span>
              </a>
              <hr className="my-2 border-gray-800" />
              <button
                className="flex items-center space-x-3 px-4 py-2.5 hover:bg-red-900/20 transition-colors w-full text-left"
              >
                <FiLogOut className="text-red-500" />
                <span className="text-sm text-red-500">Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
