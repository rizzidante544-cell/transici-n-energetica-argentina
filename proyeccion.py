import matplotlib.pyplot as plt
import numpy as np

years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]

termica =   [74, 73, 71, 70, 68, 66, 65, 63, 62, 61]
hidro =     [18, 17, 18, 17, 16, 17, 16, 16, 17, 16]
eolica =    [1,  1,  2,  3,  4,  5,  6,  7,  8,  10]
solar =     [0,  0,  0,  1,  1,  1,  2,  2,  3,  3]
nuclear =   [7,  9,  9,  9, 11, 11, 11, 12,  10, 10]

years2 = [2024, 2027, 2031, 2035]

termica2 =  [61, 50, 35, 10]
hidro2 =    [16, 15, 14, 13]
eolica2 =   [10, 15, 24, 32]
solar2 =    [3,  7,  11, 18]
nuclear2 =  [10, 10, 11, 20]
wte2 =      [0,  3,  5,  7]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

ax1.stackplot(years, termica, hidro, nuclear, eolica, solar,
              labels=['Térmica fosil', 'Hidro', 'Nuclear', 'Eólica', 'Solar'],
              colors=['#c0392b', '#2980b9', '#8e44ad', '#27ae60', '#f39c12'])
ax1.set_title('Matriz Eléctrica 2015–2024 (Actual)', fontsize=13)
ax1.set_xlabel('Año')
ax1.set_ylabel('Participación (%)')
ax1.legend(loc='lower left')

ax2.stackplot(years2, termica2, hidro2, nuclear2, eolica2, solar2, wte2,
              labels=['Térmica fosil', 'Hidro', 'Nuclear', 'Eólica', 'Solar', 'WtE'],
              colors=['#c0392b', '#2980b9', '#8e44ad', '#27ae60', '#f39c12', '#7f8c8d'])
ax2.set_title('Proyección 2024–2035 ', fontsize=13)
ax2.set_xlabel('Año')
ax2.legend(loc='lower left')

plt.suptitle('Transición Energética Argentina', fontsize=15, fontweight='bold')
valores_2035 = [10, 13, 20, 32, 18, 7]
labels_2035 = ['Térmica fósil', 'Hidro', 'Nuclear', 'Eólica', 'Solar', 'WtE']
acumulado = 0
for val, lab in zip(valores_2035, labels_2035):
    centro = acumulado + val / 2
    ax2.annotate(f'{lab}: {val}%',
                 xy=(2035, centro),
                 xytext=(2034.2, centro),
                 fontsize=8, va='center',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=1))
    acumulado += val
    
plt.tight_layout()
plt.savefig('transicion_energetica.png', dpi=150)
plt.show()

