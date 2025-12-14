# Fix Instructions - You're in the Wrong Directory!

## The Problem

You're currently in the **root `Botuvic` directory**, but you need to be in the **`cli` directory** where the virtual environment is located.

## Solution - Run These Commands:

```bash
# 1. Go into the cli directory
cd cli

# 2. Activate the virtual environment
source venv/bin/activate

# 3. Install the package
python3 -m pip install -e .

# 4. Run BOTUVIC
botuvic
```

## Step-by-Step Explanation

### Step 1: Navigate to CLI Directory
```bash
cd cli
```
**Why:** The `venv` folder is inside the `cli` directory, not the root.

### Step 2: Activate Virtual Environment
```bash
source venv/bin/activate
```
**Why:** This activates the Python virtual environment. You should see `(venv)` in your prompt after this.

### Step 3: Install Package
```bash
python3 -m pip install -e .
```
**Why:** This installs the `botuvic` command in the virtual environment.

### Step 4: Run BOTUVIC
```bash
botuvic
```
**Why:** Now the command is available!

## Quick One-Liner

If you want to do it all at once:

```bash
cd cli && source venv/bin/activate && python3 -m pip install -e . && botuvic
```

## Verify You're in the Right Place

After `cd cli`, you should see:
```bash
chaffanjutt@Affans-MacBook-Air cli %
```

And after `source venv/bin/activate`, you should see:
```bash
(venv) chaffanjutt@Affans-MacBook-Air cli %
```

## If It Still Doesn't Work

Try the helper script:
```bash
cd cli
./run.sh
```

