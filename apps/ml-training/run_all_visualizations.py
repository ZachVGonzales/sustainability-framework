"""
Master script to generate all poster graphics at once.
Run this to create all visualizations in one go.
"""

import sys
import subprocess
from pathlib import Path

print("=" * 60)
print("🎨 POSTER GRAPHICS GENERATOR")
print("=" * 60)

scripts = [
    ("visualization.py", "Core Visualizations"),
    ("advanced_visualization.py", "Advanced Metrics"),
    ("dashboard_visualization.py", "Dashboard & Infographic"),
]

print("\nRunning all visualization scripts...\n")

for script, description in scripts:
    script_path = Path(script)
    if not script_path.exists():
        print(f"⚠️  {script} not found, skipping...")
        continue
    
    print(f"▶️  Running {description} ({script})...")
    try:
        subprocess.run([sys.executable, script], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script}: {e}")
    print()

output_dir = Path("poster_graphics")
if output_dir.exists():
    graphics = list(output_dir.glob("*.png"))
    print("=" * 60)
    print(f"✨ SUCCESS! Generated {len(graphics)} graphics:")
    print("=" * 60)
    for graphic in sorted(graphics):
        size_mb = graphic.stat().st_size / (1024 * 1024)
        print(f"  ✓ {graphic.name} ({size_mb:.2f} MB)")
    print()
    print(f"📁 All graphics saved to: {output_dir.absolute()}")
    print("Ready to use on your poster! 🎉")
else:
    print("❌ poster_graphics directory not created")
