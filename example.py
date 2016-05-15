import matplotlib
matplotlib.use('module://tabbed_backend.backend_gtk3_notebook')

import matplotlib.pyplot as plt

f1 = plt.figure()
plt.plot([1,2,3])

f2 = plt.figure()
plt.plot([3, 2, 1])

f3 = plt.figure()
plt.plot([3, 2, 3])


manager = f1.canvas.manager
manager.detach_figure(f1)

plt.show()
