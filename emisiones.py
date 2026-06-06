import matplotlib.pyplot as plt
years = [2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035]
emisiones = [52, 50, 48, 46, 43, 40, 38, 36, 33, 31, 29, 28]
renovables = [16, 18, 21, 25, 28, 31, 35, 38, 43, 48, 51, 55]

fig, ax1 = plt.subplots(figsize=(10, 6))

ax1.fill_between(years, emisiones, alpha=0.3, color='#c0392b')
ax1.plot(years, emisiones, color='#c0392b', linewidth=2.5, marker='o', label='Emisiones CO₂ (Mt)')
ax1.set_xlabel('Año')
ax1.set_ylabel('Emisiones CO₂ (Mt)', color='#c0392b')
ax1.tick_params(axis='y', labelcolor='#c0392b')

ax2 = ax1.twinx()
ax2.fill_between(years, renovables, alpha=0.15, color='#27ae60')
ax2.plot(years, renovables, color='#27ae60', linewidth=2.5, marker='s', label='% Renovables')
ax2.set_ylabel('Participación Renovables (%)', color='#27ae60')
ax2.tick_params(axis='y', labelcolor='#27ae60')

# Etiquetas solo en puntos originales
years_label = [2024, 2027, 2031, 2035]
emisiones_label = [52, 46, 36, 28]
renovables_label = [16, 25, 38, 55]

for x, y in zip(years_label, emisiones_label):
    ax1.annotate(f'{y} Mt', xy=(x, y), xytext=(x, y-4),
                 fontsize=8, ha='center',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=1))

for x, y in zip(years_label, renovables_label):
    ax2.annotate(f'{y}%', xy=(x, y), xytext=(x, y+2),
                 fontsize=8, ha='center',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=1))


ax1.set_title('Reducción de Emisiones vs Crecimiento Renovable\nArgentina 2024–2035', fontsize=13)
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left')

plt.tight_layout()
plt.savefig('emisiones.png', dpi=150)
plt.show()