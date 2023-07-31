#include "ns3/core-module.h"


/**
 * File with the different physical scenarios (position of UE(s) and building(s)),
 * it also handles the movement and other variables.
*/

using namespace ns3;


    enum PhysicalDistributionOptions {
        DEFAULT,
        TREES,
        IND_ROUTER
    };
    
    /**
     * @brief Function to print a distribution information as a JSON file so we can graph the
     * scenario later, it should be function agnostic
    */
    void PrintPhysicalDistributionToJson(NodeContainer& gnbNodes, std::string extraData="\"istree\" : 0" );

    /**
     * The DEFAULT scenario, it is 2 buildings with one or more UEs that move in the same path
     * 
     *                  Antenna
     *              
     *          ---              ---
     *          |B|              |B|
     *          ---              ---
     * 
     *     UE --> .  .  .  .  .  .  .  .  .
    */
    void DefaultPhysicalDistribution(ns3::NodeContainer& gnbNodes, ns3::NodeContainer& ueNodes, double mobility);


    /**
     * Tree scenario, it is a row of 7 trees with one or more UEs that move in the same path
     * - Distance between trees: 2 meters (x axis)
     * - Each tree is modeled as a wood building of 0.5x0.5 m^2 with no internal apartments
     * - Tree height is 7 meters
     * 
     *                  Antenna
     *              
     *     ---   ---   ---   ---   ---   ---   ---
     *     |T|   |T|   |T|   |T|   |T|   |T|   |T|
     *     ---   ---   ---   ---   ---   ---   ---    -
     *                                                | 4 meters 
     *     UE --> .  .  .  .  .  .  .  .  .  .  .     -
     * 
    */
    void TreePhysicalDistribution(ns3::NodeContainer& gnbNodes, ns3::NodeContainer& ueNodes, double mobility);

    /**
     * Indoor router distribution, there is a 5G Router located and fixed inside an apartment in a
     * building that has 10 floors and there are 6 apartments per floor, the distribution is as follows.
     * The router can be placed in any of the apartments and is a residential building.
     * 
     * 
     * 
     *                      Antenna
     * 
     * 
     *      ---------------------------------------------
     *      |             |              |              |
     *      |     Apt1    |     Apt2     |     Apt3     |
     *      |             |              |              |
     *      ---------------------------------------------
     *      |             |              |              |
     *      |     Apt4    |     Apt5     |     Apt6     |   
     *      |             |              |              |
     *      ---------------------------------------------
     * 
    */
    void IndoorRouterPhysicalDistribution(ns3::NodeContainer& gnbNodes, ns3::NodeContainer& ueNodes);

