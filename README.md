# College Fee Management System Pro

Windows desktop starter project for Bus Fee + Semester Fee management.

## Confirmed fee rules
- Semester duration: 6 months
- General: ₹27,000 per semester
- Reserved: ₹23,250 per semester
- Late fine: ₹100 after the 10th, once for each generated student/month charge
- Bus fee: monthly amount entered per student

## Features
- Dashboard totals: students, total charges, collected, pending fees, pending students
- Student records with category, course, semester, bus route and monthly bus fee
- Generate monthly Bus charges
- Generate 6-month Semester charges
- Full and partial payment entries
- Payment history and text receipt
- CSV export for students, charges and payments (Excel-compatible)
- Manual SQLite database backup

## Build without installing Python on your PC
1. Create a new GitHub repository.
2. Upload all files and folders from this project. Keep `.github/workflows/build-windows.yml` at that exact path.
3. Open the repository's **Actions** tab.
4. Select **Build Windows EXE** → **Run workflow**.
5. Wait for the green successful run.
6. Open that run, scroll to **Artifacts**, and download `CollegeFeeManagementSystemPro-Windows`.
7. Extract the ZIP and run `CollegeFeeManagementSystemPro.exe`.

Python is installed only on GitHub's temporary build machine, not on your computer.

## First use
1. Open Students and add students. Select General or Reserved.
2. Enter each student's monthly Bus Fee if applicable.
3. Open Fee Charges and enter a period as `YYYY-MM`.
4. Click Generate Bus Fee for the month and/or Generate Semester Fee.
5. Semester charges use the student's category and the fixed semester fee.
6. Open Record Payment, select a pending charge, enter the amount and save.
7. Use Reports & Export for CSV files and database backup.

## Data location
The EXE stores its database in:
`%LOCALAPPDATA%\\CollegeFeeManagementSystemPro\\college_fees.db`

Keep backups before moving to another computer or reinstalling Windows.

## Important limitations of this starter build
- This is a local, single-PC application. No login/multi-user sync or automatic Google Drive backup is included.
- Receipts are saved as `.txt`; PDF receipt printing, institution logo, configurable fee structures and advanced month-wise dues automation are future enhancements.
- The late fine is applied when a charge is generated after day 10 for the current month. The application prevents duplicate charges for the same student/type/period.
- Review the fee policy with the college before generating real student charges.
