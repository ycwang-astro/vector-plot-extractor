# CHANGELOG

## 0.1.3
### Bugs fixed
- Fix "bottom-left" position of Matplotlib `Rectangle`. This bug affects `.sel.obj` files, and results in an offset in all rectangles in the plot. 2nd step need to be re-run ("Re-selecting") to fix `.sel.obj`. It seems that other files, including the exported data, are not affected by this bug.
- Fix bugs with the display of certain types of plot elements

### Improvements
- Supports paths combining type 'c' (Bezier curve) and 'l' (line). (Fixes [issue #1](https://github.com/ycwang-astro/vector-plot-extractor/issues/1))
- Show information if find nothing to extract
- Supports line-like scatter markers; show warning if labeling line-like as scatter

### Modifications
- `.out` file includes package version that exports the data
- Add `DataExplorer.plot()`

## 0.1.2
### Urgent bug fix
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
