pi+_0 [type=pi+];
pi+_1 [type=pi+];
pi-_0 [type=pi-];
pi-_1 [type=pi-];
pi-_2 [type=pi-];
pi-_3 [type=pi-];
K+_0 [type=K+];
K+_1 [type=K+];

B0 -> {D1 D* K-};
D1 -> {D*- pi+_0};

D*- -> {D0 pi-_0};
D0 -> {K+_0 pi-_1 pi0};
K+_1 -> {}; # Generic
D* -> {D+ pi-_2};
D+ -> {K+_1 pi+_1 pi-_3};