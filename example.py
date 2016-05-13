import matplotlib
matplotlib.use('module://tabbed_backend.backend_gtk3_notebook')

import matplotlib.pyplot as plt

f = plt.figure()
plt.plot([1,2,3])

f2 = plt.figure()
plt.plot([3, 2, 1])

plt.show()
