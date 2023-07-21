#include "ns3/core-module.h"
#include "ns3/applications-module.h"
#include <ns3/antenna-module.h>
#include <ns3/buildings-helper.h>
#include <ns3/buildings-module.h>
#include <ns3/mobility-module.h>
#include "ns3/nr-module.h"
#include "cmdline-colors.h"


/**
 * File with the different physical scenarios (position of UE(s) and building(s)),
 * it also handles the movement and other variables.
*/

namespace ns3
{

    enum PhysicalDistributionOptions {
        DEFAULT,
        OPTION2,
        OPTION3
    } phydistribution_t;
    
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





void DefaultPhysicalDistribution(ns3::NodeContainer& gnbNodes, ns3::NodeContainer& ueNodes, double mobility)
{
    
    double speed = 1;               // in m/s for walking UT.
    std::string scenario = "UMa";   // scenario
    double hBS;          // base station antenna height in meters
    double hUE;          // user antenna height in meters

    // set mobile device and base station antenna heights in meters, according to the chosen scenario
    if (scenario == "UMa") {
        hBS = 25;
        hUE = 1.5;

    } else {
        NS_ABORT_MSG("Scenario not supported. Only UMa is currently supported");
    }

    // RB Info and position
    uint16_t gNbNum = 1;    // Numbers of RB
    double gNbX = 50.0;     // X position
    double gNbY = 50.0;     // Y position
    uint16_t gNbD = 80;     // Distance between gNb

    // UE Info and position
    uint16_t ueNumPergNb = 1;   // Numbers of User per RB
    double ueDistance = .50;    //Distance between UE
    double xUE=30;  //Initial X Position UE
    double yUE=10;  //Initial Y Position UE

    // BUILDING Position
    bool enableBuildings = true; // 
    uint32_t gridWidth = 3 ;//
    uint32_t numOfBuildings = 2;
    uint32_t apartmentsX = 1;
    uint32_t nFloors = 10;

    double buildX=37.0; // Initial X Position
    double buildY=30.0; // Initial Y Position
    double buildDx=10;  // Distance X between buildings
    double buildDy=10;  // Distance Y between buildings
    double buildLx=8;   // X Length
    double buildLy=10;  // Y Length

    // Set position of the base stations
    std::cout << cyan << "Positioning Nodes" << clear << std::endl;
    Ptr<ListPositionAllocator> gnbPositionAlloc = CreateObject<ListPositionAllocator>();
    for (uint32_t u = 0; u < gnbNodes.GetN(); ++u)
    {
        std::cout << "Node ID " << gnbNodes.Get (u)->GetId() << " Sys ID:" << gnbNodes.Get(u)->GetSystemId() + u << std::endl;
        std::cout << "gNb: " << u << "\t" << "(" << gNbX << "," << gNbY+gNbD*u <<")" << std::endl;
        gnbPositionAlloc->Add(Vector(gNbX, gNbY+gNbD*u, hBS));
    }
    MobilityHelper enbmobility;
    enbmobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    enbmobility.SetPositionAllocator(gnbPositionAlloc);
    enbmobility.Install(gnbNodes);

    // position the mobile terminals and enable the mobility
    MobilityHelper uemobility;
    uemobility.SetMobilityModel("ns3::ConstantVelocityMobilityModel");
    // uemobility.SetMobilityModel("ns3::RandomDirection2dMobilityModel","Bounds", RectangleValue(Rectangle(x_min, x_max, y_min, y_max)));
    // uemobility.SetMobilityModel("ns3::WaypointMobilityModel");
    uemobility.Install(ueNodes);

    if (!mobility){
        speed=0;
    }
 
    // Set Initial Position of UE
    for (uint32_t u = 0; u < ueNodes.GetN(); ++u)
    {
        std::cout << "UE: " << u << "\t" << "Pos: "<<"(" << xUE << "," << yUE +ueDistance*u <<")" << "\t" << "Speed: (" << speed << ", 0)" <<std::endl;
        ueNodes.Get(u)->GetObject<MobilityModel>()->SetPosition(Vector((float)xUE, (float) yUE +(float)ueDistance*u, hUE)); // (x, y, z) in m
        ueNodes.Get(u)->GetObject<ConstantVelocityMobilityModel>()->SetVelocity(Vector( speed, 0,  0)); // move UE1 along the x axis

        // Waypoint model
        // Ptr<WaypointMobilityModel> waypoints = ueNodes.Get(u)->GetObject<WaypointMobilityModel>();
        // waypoints->AddWaypoint(Waypoint (Seconds(0.0), Vector(xUE, yUE, hUE))); // Posición inicial
        // waypoints->AddWaypoint(Waypoint (Seconds(10.0), Vector(xUE-5, yUE-10, hUE)));
        // waypoints->AddWaypoint(Waypoint (Seconds(20.0), Vector(xUE, yUE, hUE))); // Posición final
    }
    #pragma endregion UE_gNB

    /********************************************************************************************************************
     * Create and install buildings
     ********************************************************************************************************************/
    if (enableBuildings)
    {
        std::cout << cyan << "Installing Building" << clear << std::endl;

        Ptr<GridBuildingAllocator> gridBuildingAllocator;
        gridBuildingAllocator = CreateObject<GridBuildingAllocator>();
        gridBuildingAllocator->SetAttribute("GridWidth", UintegerValue(gridWidth)); // The number of objects laid out on a line. 1 as a column of building
        gridBuildingAllocator->SetAttribute("MinX", DoubleValue(buildX)); // The x coordinate where the grid starts.
        gridBuildingAllocator->SetAttribute("MinY", DoubleValue(buildY)); // The y coordinate where the grid starts.
        gridBuildingAllocator->SetAttribute("LengthX", DoubleValue(buildLx * apartmentsX)); // the length of the wall of each building along the X axis.
        gridBuildingAllocator->SetAttribute("LengthY", DoubleValue(buildLy)); // the length of the wall of each building along the X axis.
        gridBuildingAllocator->SetAttribute("DeltaX", DoubleValue(buildDx)); // The x space between buildings.
        gridBuildingAllocator->SetAttribute("DeltaY", DoubleValue(buildDy)); // The y space between buildings.
        gridBuildingAllocator->SetAttribute("Height", DoubleValue(3 * nFloors)); // The height of the building (roof level)
        gridBuildingAllocator->SetAttribute("LayoutType", EnumValue (GridPositionAllocator::ROW_FIRST)); // The type of layout. ROW_FIRST COLUMN_FIRST

        gridBuildingAllocator->SetBuildingAttribute("NRoomsX", UintegerValue(apartmentsX));
        gridBuildingAllocator->SetBuildingAttribute("NRoomsY", UintegerValue(1));
        gridBuildingAllocator->SetBuildingAttribute("NFloors", UintegerValue(nFloors));
        gridBuildingAllocator->Create(numOfBuildings);

        // position of the Buildings
        Ptr<ListPositionAllocator> buildingPositionAlloc = CreateObject<ListPositionAllocator>();
        buildingPositionAlloc->Add(Vector(buildX, buildY, 0.0));
        MobilityHelper buildingmobility;
        buildingmobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
        buildingmobility.SetPositionAllocator(buildingPositionAlloc);

        BuildingsHelper::Install(gnbNodes);
        BuildingsHelper::Install(ueNodes);

        std::cout << "Installed via function" << std::endl;

    }
}


} // namespace ns3