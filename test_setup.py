packages = {
    "gymnasium": "gymnasium",
    "stable_baselines3": "stable_baselines3",
    "torch": "torch",
    "tensorflow": "tensorflow",
    "sklearn": "scikit-learn",
    "pandas": "pandas",
    "numpy": "numpy",
    "faiss": "faiss",
    "shap": "shap",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
}

all_ok = True
for import_name, display_name in packages.items():
    try:
        mod = __import__(import_name)
        version = getattr(mod, "__version__", "installed")
        print(f"  ✅  {display_name:<25} {version}")
    except ImportError:
        print(f"  ❌  {display_name:<25} NOT FOUND")
        all_ok = False

print()
if all_ok:
    print("✅ ALL PACKAGES OK — Day 1 setup complete!")
else:
    print("❌ Some packages missing")
