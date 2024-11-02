import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d

# Parâmetros do pneu e transmissão
g = 9.8     # Aceleração da gravidade [m/s²]
R = 0.25    # Raio dinâmico do pneu [m]
G = 1     # Relação de marcha do câmbio
A = 0.6     # Coeficiente quadrático da resistência do ar
B = 0.01    # Coeficiente linear da resistência do ar
C = 200      # Constante da resistência do ar
f = 0.015   # Coeficiente de resistência à rolagem
Total_mass = 250  # Massa total [kg]

# Leitura dos dados do motor e CVT
engine_df = pd.read_csv("engine_data_S19.csv")
cvt_df = pd.read_csv("cvt_ideal.csv")

# Curvas do motor
engine_curve_engine_speed = engine_df["Engine Speed [RPM]"]
engine_curve_engine_torque = engine_df["Corrected Torque [N.m]"]

# Curvas do CVT
cvt_curve_vehicle_speed = cvt_df["Vehicle Speed [m/s]"]
cvt_curve_engine_speed = cvt_df["Engine Speed [RPM]"]

# Interpolação das curvas usando interpolação linear
engine_curve_engine_torque_interpol = interp1d(engine_curve_engine_speed, engine_curve_engine_torque, kind='linear', fill_value="extrapolate")
cvt_curve_engine_speed_interpol = interp1d(cvt_curve_vehicle_speed, cvt_curve_engine_speed, kind='linear', fill_value="extrapolate")

# Parâmetros de simulação
T_max = 30  # Tempo máximo da simulação [s]
T_step = 0.2  # Passo do tempo [s]

# Lista para armazenar resultados de velocidade e deslocamento
Speed_List = []  # Para armazenar as velocidades ao longo do tempo
Distance_List = []  # Para armazenar deslocamento ao longo do tempo
Time_List = []  # Para armazenar o tempo

initial_speed_kmh = 3  # Velocidade inicial [km/h]
initial_vehicle_speed = initial_speed_kmh / 3.6  # Conversão para m/s
instant_vehicle_speed = initial_vehicle_speed  # Reinicia a velocidade inicial
Total_Length_travelled = 0  # Inicializa o deslocamento

# Simulação do movimento do veículo
for t in np.arange(0, T_max, T_step):
    Speed_List.append(instant_vehicle_speed * 3.6)  # Armazenar em km/h
    Distance_List.append(Total_Length_travelled)
    Time_List.append(t)  # Armazenar o tempo

    instant_engine_speed = cvt_curve_engine_speed_interpol(instant_vehicle_speed)
    instant_engine_torque = engine_curve_engine_torque_interpol(instant_engine_speed)

    # Evitar divisão por zero no cálculo da razão da CVT
    if instant_vehicle_speed != 0:
        instant_cvt_ratio = instant_engine_speed * 2 * np.pi / (60 * G) * R / instant_vehicle_speed
        
        # Condições para limitar a razão da CVT
        if instant_cvt_ratio < 1:
            instant_cvt_ratio = 1
        elif instant_cvt_ratio > 4:
            instant_cvt_ratio = 4
    else:
        instant_cvt_ratio = 1  # Tratar divisão por zero

    instant_proppeling_force = 0.85 * (instant_engine_torque * G * instant_cvt_ratio) / R
    instant_road_load = A * instant_vehicle_speed ** 2 + B * instant_vehicle_speed + C

    # Cálculo da força líquida
    instant_net_force = instant_proppeling_force - instant_road_load

    # Cálculo da aceleração e atualização da velocidade
    instant_vehicle_acceleration = instant_net_force / Total_mass
    instant_vehicle_speed += instant_vehicle_acceleration * T_step

    # Evitar velocidade negativa
    if instant_vehicle_speed < 0:
        instant_vehicle_speed = 0

    Total_Length_travelled += instant_vehicle_speed * T_step + instant_vehicle_acceleration/2 * T_step**2 # Atualiza o deslocamento




























# Plotar resultados
plt.figure(figsize=(18, 5))

# Gráfico de Velocidade em km/h
plt.subplot(1, 3, 1)
plt.plot(Time_List, Speed_List, marker='o')
plt.xlabel("Tempo [s]")
plt.ylabel("Velocidade [km/h]")
plt.title("Velocidade do Veículo ao Longo do Tempo")
plt.xlim(0, T_max)
plt.ylim(0, max(Speed_List) + 5)  # Ajustar limite superior
plt.grid(True)

# Gráfico de Velocidade por Deslocamento
plt.subplot(1, 3, 2)
plt.plot(Distance_List, Speed_List, marker='o')
plt.xlabel("Deslocamento [m]")
plt.ylabel("Velocidade [km/h]")
plt.title("Velocidade do Veículo em Função do Deslocamento")
plt.grid(True)

# Gráfico de Deslocamento em Função do Tempo
plt.subplot(1, 3, 3)
plt.plot(Time_List, Distance_List, marker='o', label='Deslocamento')
plt.axhline(y=30, color='r', linestyle='--', label='30 m')
plt.axhline(y=100, color='g', linestyle='--', label='100 m')
plt.xlabel("Tempo [s]")
plt.ylabel("Deslocamento [m]")
plt.title("Deslocamento do Veículo ao Longo do Tempo")
plt.legend()
plt.xlim(0, T_max)
plt.grid(True)

plt.tight_layout()
plt.show()
