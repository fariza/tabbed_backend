import matplotlib
matplotlib.use('module://tabbed_backend.backend_gtk3_notebook')

import matplotlib.pyplot as plt

f1 = plt.figure()
plt.plot([1, 2, 3])

# f2 = plt.figure(manager=False)
f2 = plt.figure()
plt.plot([3, 2, 1])

f3 = plt.figure()
plt.plot([3, 2, 3])

f1.canvas.manager.detach()

plt.show()
