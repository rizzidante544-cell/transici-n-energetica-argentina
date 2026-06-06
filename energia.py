import matplotlib.pyplot as plt
import numpy as np

years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]

termica =   [74, 73, 71, 70, 68, 66, 65, 63, 62, 61]
hidro =     [18, 17, 18, 17, 16, 17, 16, 16, 17, 16]
eolica =    [1,  1,  2,  3,  4,  5,  6,  7,  8,  10]
solar =     [0,  0,  0,  1,  1,  1,  2,  2,  3,  3]
nuclear =   [7,  9,  9,  9, 11, 11, 11, 12,  10, 10]

plt.figure(figsize=(12, 6))
plt.stackplot(years, termica, hidro, nuclear, eolica, solar,
              labels=['Térmica', 'Hidro', 'Nuclear', 'Eólica', 'Solar'],
              colors=['#c0392b', '#2980b9', '#8e44ad', '#27ae60', '#f39c12'])

plt.title('Matriz Eléctrica Argentina 2015–2024 (% generación)', fontsize=14)
plt.xlabel('Año')
plt.ylabel('Participación (%)')
plt.legend(loc='lower left')
plt.tight_layout()
plt.savefig('matriz_energetica.png', dpi=150)
plt.show()
