import { useState, useEffect } from 'react';

const useAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem('Token');
      setIsAuthenticated(!!token); // টোকেন থাকলে true, না থাকলে false
    };

    checkAuth(); // প্রথমবার চেক করা

    // স্টোরেজ চেঞ্জ হলে (যেমন অন্য ট্যাব থেকে লগআউট) অটো চেক
    window.addEventListener('storage', checkAuth);

    // ক্লিনআপ
    return () => {
      window.removeEventListener('storage', checkAuth);
    };
  }, []);

  return { isAuthenticated };
};

export default useAuth;