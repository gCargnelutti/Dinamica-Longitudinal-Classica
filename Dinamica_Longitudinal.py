import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d


J13_Data = [
    {"nome": "Prototipo", "valor": "J13", "unidade": "", "descricao": "Nome do protótipo"},
    {"nome": "R", "valor": 0.25, "unidade": "m", "descricao": "Raio dinâmico do pneu"},
    {"nome": "G", "valor": 8.5, "unidade": "", "descricao": "Relação de marcha do câmbio"},
    {"nome": "A", "valor": 0.8, "unidade": "", "descricao": "Coeficiente quadrático da resistência do ar"},
    {"nome": "B", "valor": 0.01, "unidade": "", "descricao": "Coeficiente linear da resistência do ar"},
    {"nome": "C", "valor": 0.015, "unidade": "", "descricao": "Coeficiente de resistência à rolagem"},
    {"nome": "M", "valor": 320, "unidade": "kg", "descricao": "Massa total"}, #falta considerar inercia.
    {"nome": "engine_data_path", "valor": "engine_data_S19.csv", "unidade": "", "descricao": "Caminho do arquivo de dados do motor"},
    {"nome": "cvt_data_path", "valor": "cvt_ideal.csv", "unidade": "", "descricao": "Caminho do arquivo de dados da CVT"}
]

def Analise(Car_Data):

    #Parâmetros de simulação
    T_max = 30  # Tempo máximo da simulação [s]
    T_step = 0.2  # Passo do tempo [s]
    instant_vehicle_speed = 3 / 3.6  #Inicia a velocidade em 3 km/h
    Total_Length_travelled = 0  # Inicializa o deslocamento
    g = 9.8 #Aceleração da gravidade

    #Lista auxiliares para armazenar resultados de velocidade e deslocamento
    Speed_List = []  # Para armazenar as velocidades ao longo do tempo
    Distance_List = []  # Para armazenar deslocamento ao longo do tempo
    Time_List = []  # Para armazenar o tempo

    #Variaveis auxiliares para a analise de velocidade em 100m:
    m_100 = 100  # Distância alvo 100m
    closest_speed_100 = None  # Velocidade no ponto mais próximo a 100m
    min_distance_diff_100 = float('inf')  # Diferença mínima em relação a 100m

    #Variaveis auxiliares para a analise de aceleracao:
    m_30 = 30  # Distância alvo 30m
    closest_time_30 = None  #Tempo no ponto mais próximo a 30m
    min_distance_diff_30 = float('inf')  # Diferença mínima em relação a 30m

    #Parametros do veiculo:
    R = next(item['valor'] for item in Car_Data if item['nome'] == "R")
    G = next(item['valor'] for item in Car_Data if item['nome'] == "G")
    A = next(item['valor'] for item in Car_Data if item['nome'] == "A")
    B = next(item['valor'] for item in Car_Data if item['nome'] == "B")
    C = next(item['valor'] for item in Car_Data if item['nome'] == "C")
    M = next(item['valor'] for item in Car_Data if item['nome'] == "M")
    engine_data_path = next(item['valor'] for item in Car_Data if item['nome'] == "engine_data_path")
    cvt_data_path = next(item['valor'] for item in Car_Data if item['nome'] == "cvt_data_path")

    #Curvas do motor:
    engine_df = pd.read_csv(engine_data_path)
    engine_curve_engine_speed = engine_df["Engine Speed [RPM]"]
    engine_curve_engine_torque = engine_df["Corrected Torque [N.m]"]

    #Curvas da CVT
    cvt_df = pd.read_csv(cvt_data_path)
    cvt_curve_vehicle_speed = cvt_df["Vehicle Speed [m/s]"]
    cvt_curve_engine_speed = cvt_df["Engine Speed [RPM]"]

    #Interpolação das curvas usando interpolação linear
    engine_curve_engine_torque_interpol = interp1d(engine_curve_engine_speed, engine_curve_engine_torque, kind='linear', fill_value="extrapolate")
    cvt_curve_engine_speed_interpol = interp1d(cvt_curve_vehicle_speed, cvt_curve_engine_speed, kind='linear', fill_value="extrapolate")



    # Simulação do movimento do veículo
    for t in np.arange(0, T_max, T_step):
        Speed_List.append(instant_vehicle_speed * 3.6)  # Armazenar em km/h
        Distance_List.append(Total_Length_travelled)
        Time_List.append(t)  # Armazenar o tempo

        instant_engine_speed = cvt_curve_engine_speed_interpol(instant_vehicle_speed)
        instant_engine_torque = engine_curve_engine_torque_interpol(instant_engine_speed)

        # Evitar divisão por zero no cálculo da razão da CVT
        if instant_vehicle_speed != 0:
            instant_cvt_ratio = (instant_engine_speed * 2 * np.pi * R) / (G * 60 * instant_vehicle_speed)
            
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
        instant_vehicle_acceleration = instant_net_force / M
        instant_vehicle_speed += instant_vehicle_acceleration * T_step

        # Evitar velocidade negativa
        if instant_vehicle_speed < 0:
            instant_vehicle_speed = 0

        Total_Length_travelled += instant_vehicle_speed * T_step #Atualiza o deslocamento




        #Verifica a distância percorrida para a velocidade em 100m
        distance_diff_100 = abs(Total_Length_travelled - m_100)
        if distance_diff_100 < min_distance_diff_100:
            min_distance_diff_100 = distance_diff_100
            closest_speed_100 = instant_vehicle_speed * 3.6  # Armazenar em km/h

        #Verifica a distância percorrida para a aceleracao:
        distance_diff_30 = abs(Total_Length_travelled - m_30)
        if distance_diff_30 < min_distance_diff_30:
            min_distance_diff_30 = distance_diff_30
            closest_time_30 = t



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

    print(closest_time_30)

Analise(J13_Data)



















