"use client";

import { useEffect, useState } from "react";

const KEY = "designer-mode";

export function DesignerToggle() {
  const [on, setOn] = useState(false);
  useEffect(() => {
    setOn(localStorage.getItem(KEY) === "1");
  }, []);
  function toggle() {
    const next = !on;
    setOn(next);
    if (next) localStorage.setItem(KEY, "1");
    else localStorage.removeItem(KEY);
  }
  return (
    <label className="toggle">
      <input type="checkbox" checked={on} onChange={toggle} />
      <span>Conversation designer mode is {on ? "on" : "off"}</span>
    </label>
  );
}
