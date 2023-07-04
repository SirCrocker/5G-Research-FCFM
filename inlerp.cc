#include "ns3/nr-eesm-t1.h"
#include <fstream>

std::string infostr = R"V0G0N(// Copyright (c) 2022 Centre Tecnologic de Telecomunicacions de Catalunya (CTTC)
// Interpolated by the ProbeBLER crew (asado?)
// SPDX-License-Identifier: GPL-2.0-only

#include "ns3/nr-eesm-t1.h"

namespace ns3
{

/**
 * \brief Table of SE of the standard MCSs: 29 (0 to 28) MCSs as per Table1 in TS38.214
 */
static const std::vector<double> SpectralEfficiencyForMcs1 = {
    // QPSK (M=2)
    0.23,
    0.31,
    0.38,
    0.49,
    0.6,
    0.74,
    0.88,
    1.03,
    1.18,
    1.33, // SEs of MCSs
    // 16QAM (M=4)
    1.33,
    1.48,
    1.70,
    1.91,
    2.16,
    2.41,
    2.57, // SEs of MCSs
    // 64QAM (M=6)
    2.57,
    2.73,
    3.03,
    3.32,
    3.61,
    3.90,
    4.21,
    4.52,
    4.82,
    5.12,
    5.33,
    5.55 // SEs of MCSs
};

/**
 * \brief Table of SE of the standard CQIs: 16 CQIs as per Table1 in TS38.214
 */
static const std::vector<double> SpectralEfficiencyForCqi1 = {0.0, // out of range
                                                            0.15,
                                                            0.23,
                                                            0.38,
                                                            0.6,
                                                            0.88,
                                                            1.18,
                                                            1.48,
                                                            1.91,
                                                            2.41,
                                                            2.73,
                                                            3.32,
                                                            3.9,
                                                            4.52,
                                                            5.12,
                                                            5.55};

/**
 * \brief SINR to BLER mapping for MCSs in Table1
 */)V0G0N";


using namespace ns3;

std::vector<std::vector<double>> interpolarPuntos(const std::vector<double>& X, const std::vector<double>& Y, int n);

int main()
{
    NrEesmT1 table;
    auto* tt = table.m_simulatedBlerFromSINR;

    auto a = std::get<1>(tt->at(1).at(6).at(704));
    
    int mcsIndex = 0;
    int BsgIndex = 0;

    std::ofstream outfile("new_table.cc");  
    
    outfile << infostr << std::endl;


    outfile << "static const NrEesmErrorModel::SimulatedBlerFromSINR BlerForSinr1 = {" << std::endl;

    for (const auto& BaseGrah : *tt)
    {
        outfile << "\t{ // BG TYPE " << BsgIndex << std::endl;
        for (const auto& MCS : BaseGrah)
        {
            outfile << "\t { // MCS " << mcsIndex << std::endl;
            for (const auto & CBS : MCS)
            {
                outfile << "\t  {" << CBS.first << "U, // SINR and BLER for CBS " << CBS.first << std::endl;
                auto& sinr = std::get<0>(CBS.second);
                auto& bler = std::get<1>(CBS.second);

                std::vector<std::vector<double>> interpVals = interpolarPuntos(sinr, bler, 10);

                auto sinrvector = interpVals.front();
                auto blervectro = interpVals.back();

                outfile << "\t   NrEesmErrorModel::DoubleTuple{" << std::endl;
                
                outfile << "\t    {";
                bool found_last = false;
                for (const auto& sinrval : sinrvector)
                {
                    if (sinrval == sinrvector.back() and !found_last)
                    {
                        outfile << sinrval;
                        found_last = true;
                    }
                    else if (found_last)
                    {
                        outfile << ", FOUNDLAST " << sinrval; 
                    }
                    else
                    {
                    outfile << sinrval << ", ";
                    }
                }
                found_last = false;
                outfile << "}, // SINR \n\t    {";
                for (const auto& blerval : blervectro)
                {
                    if (blerval == blervectro.back() and !found_last)
                    {
                        outfile << blerval;
                        found_last = true;
                    }
                    else if (found_last)
                    {
                        outfile << ", " << blerval; 
                    }
                    else
                    {
                    outfile << blerval << ", ";
                    }
                }
                outfile << "} // BLER" << std::endl;

                outfile << "\t   }" << std::endl;

                outfile << "\t  }," << std::endl;
            }
            
            outfile << "\t }," << std::endl;
            mcsIndex++;
        }
        

        outfile << "}," << std::endl;
        BsgIndex++;
    }
    outfile << "};" << std::endl;
    outfile << "} // namespace ns3" << std::endl;

    return 0;
}


std::vector<std::vector<double>> interpolarPuntos(const std::vector<double>& X, const std::vector<double>& Y, int n) {
    std::vector<double> sinrInterpolados;
	std::vector<double> blerInterpolados;

    int numPuntos = X.size();
    double incremento = (X[numPuntos - 1] - X[0]) / (n + 1);

    if (X.size() < 2)
    {
        std::vector<std::vector<double>> puntosInterpolados;
        puntosInterpolados.push_back(X);
		puntosInterpolados.push_back(Y);
        return puntosInterpolados;
    }

    // Agregar el primer punto original
		sinrInterpolados.push_back(X[0]);
		blerInterpolados.push_back(Y[0]);

    for (int i = 0; i < n; i++) {
        double xNuevo = X[0] + (i + 1) * incremento;

        // Encontrar los puntos de referencia más cercanos
        int j = 0;
        while (X[j] < xNuevo) {
            j++;
        }

        double x1 = X[j - 1];
        double x2 = X[j];
        double y1 = Y[j - 1];
        double y2 = Y[j];

        // Interpolación lineal
        double yNuevo = y1 + (y2 - y1) * (xNuevo - x1) / (x2 - x1);

        // Agregar el punto interpolado al vector de puntos
        sinrInterpolados.push_back(xNuevo);
		blerInterpolados.push_back(yNuevo);
    }

    // Agregar el último punto original
		sinrInterpolados.push_back(X[numPuntos - 1]);
		blerInterpolados.push_back(Y[numPuntos - 1]);
		
		std::vector<std::vector<double>> puntosInterpolados;
		puntosInterpolados.push_back(sinrInterpolados);
		puntosInterpolados.push_back(blerInterpolados);

    return puntosInterpolados;
}