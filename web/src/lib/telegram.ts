export function getTelegramWebApp() {
  return window.Telegram?.WebApp ?? null;
}

export function getInitData(): string | null {
  const wa = getTelegramWebApp();
  return wa?.initData?.length ? wa.initData : null;
}

export function tgReady() {
  const wa = getTelegramWebApp();
  if (!wa) return;
  try {
    wa.expand();
    wa.ready();
  } catch {
    // ignore
  }
}

