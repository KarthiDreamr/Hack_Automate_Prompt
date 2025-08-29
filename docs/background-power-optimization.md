### ✅ 1. Set brightness to **7**

```bash
sudo brightnessctl set 7
```

*(This sets raw brightness value to `7` out of 120000 — very dim 🔅)*

---

### ✅ 2. Inhibit sleep for **1 hour**

```bash
systemd-inhibit --what=sleep --why="Stay awake for 1 hour" --mode=block sleep 3600
```

---

🧠 **Fun Fact**: The human pupil can adjust from bright sunlight (\~10⁸ lux) to starlight (\~10⁻³ lux) — that’s like a 10 trillion times difference! Your screen just dims a little, but your eyes are absolute marvels! 👁️🌌✨


Here's the **combined command** to:

✅ Set brightness to `7` (raw value)
✅ Prevent sleep for **1 hour**

```bash
bash -c 'sudo brightnessctl set 7 && systemd-inhibit --what=sleep --why="Stay awake for 1 hour" --mode=block sleep 3600'
```

> 🛑 You’ll be prompted for your password due to `sudo`.

---

🧠 **Fun Fact**: Your Linux system can dim to *single-digit brightness values*, but early CRT monitors had no such controls — brightness had to be tuned using knobs and analog circuits! 📺⚙️🔧
