# CHANGELOG

## 0.1.2
- fix error of scatter positions induced by duplication in coords

**Notes**. A bug in version 0.1.1 causes minor errors in the extracted scatter data. If you have used 0.1.1 version, follow the below steps to fix it:
- Update to version 0.1.2
- Execute `vpextract path/to/figure/file`
- If prompted, press Enter to skip the 1st step ("Re-identifing").
- If prompted, input "y" and press Enter to redo the 2nd step ("Re-selecting"). You will have to redo this step to fix the problem.
- After redoing the 2nd step and closing the window, input "y" and press Enter to confirm overwriting the `.sel.obj` file.
- If prompted, input "y" and press Enter to confirm that the `.out` file may be overwritten.
- After the figure window appears (you should see something like "\[A\]dd an axis, ..."), press "e" to export your data to the `.out` file again.
- Now the errors in the data should be fixed.
