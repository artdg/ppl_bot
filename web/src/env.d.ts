interface Window {
  Telegram?: {
    WebApp?: {
      initData: string;
      initDataUnsafe?: unknown;
      ready: () => void;
      expand: () => void;
      close: () => void;
    };
  };
}

