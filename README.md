# X728 Power Management Setup

This folder contains all the necessary files to enable and configure **X728 power management** on a Raspberry Pi. The setup includes systemd service files, logic for power detection, safe shutdown, and integration with Signal K.

---

## 📁 Files Included
| **File**                  | **Location**               | **Purpose**                              |
|--------------------------|----------------------------|------------------------------------------|
| **x728_power_management.py** | `/usr/local/bin/`        | Main logic for power loss, battery status, and shutdowns. |
| **x728-pwr.service**        | `/etc/systemd/system/`     | systemd service to start power logic on boot. |
| **x728-shutdown.service**   | `/etc/systemd/system/`     | systemd service for handling shutdowns.  |
| **xSoft.sh** (optional)     | `/usr/local/bin/`          | Safe shutdown script (optional but useful). |

---

## 📋 Reinstallation Instructions

If you ever want to **re-enable the X728 logic**, follow these steps.

### 1️⃣ **Copy the files back to their original locations**
Run the following commands to copy files where they need to go:
```bash
sudo cp x728_power_management.py /usr/local/bin/
sudo cp x728-pwr.service /etc/systemd/system/
sudo cp x728-shutdown.service /etc/systemd/system/

# If xSoft.sh is included
if [ -f xSoft.sh ]; then
    sudo cp xSoft.sh /usr/local/bin/
fi

