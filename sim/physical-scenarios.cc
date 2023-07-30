#include <ns3/core-module.h>
#include <ns3/network-module.h>
#include <ns3/applications-module.h>
#include <ns3/antenna-module.h>
#include <ns3/buildings-helper.h>
#include <ns3/buildings-module.h>
#include <ns3/mobility-module.h>
#include "ns3/nr-module.h"
#include "cmdline-colors.h"

#include "physical-scenarios.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("PhysicalDistro");

// Currently creates a gnuplot file, to be updated later into a json file that will be 
// parseable by matplotlib. 
void 
PrintPhysicalDistributionToJson()
{
    std::string predata = R"RAW(scale = 2600/640
set terminal pngcairo size 640*scale,480*scale fontscale scale linewidth scale pointscale scale
set title "Placement of Buildings, only illustrative"
set output "./phy-distro.png"
set xrange [0:100]
set yrange [0:100])RAW";

    std::string postdata = "set nokey\nplot NaN";

    std::ofstream outFile("PhysicalDistribution.gnuplot");
    if (!outFile.is_open())
    {
        NS_LOG_ERROR("Can't open file " << "PhysicalDistribution.gnuplot");
        return;
    }
    outFile << predata << std::endl;
    uint32_t index = 0;
    for (BuildingList::Iterator it = BuildingList::Begin(); it != BuildingList::End(); ++it)
    {
        ++index;
        Box box = (*it)->GetBoundaries();
        outFile << "set object " << index << " rect from " << box.xMin << "," << box.yMin << " to "
                << box.xMax << "," << box.yMax << std::endl;
    }
    outFile << postdata << std::endl;
    outFile.close();
}

void 
DefaultPhysicalDistribution(ns3::NodeContainer& gnbNodes, ns3::NodeContainer& ueNodes, double mobility)
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
    // uint16_t gNbNum = 1;    // Numbers of RB
    double gNbX = 50.0;     // X position
    double gNbY = 50.0;     // Y position
    uint16_t gNbD = 80;     // Distance between gNb

    // UE Info and position
    // uint16_t ueNumPergNb = 1;   // Numbers of User per RB
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
    std::cout << TXT_CYAN << "Positioning Nodes" << TXT_CLEAR << std::endl;
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

    /********************************************************************************************************************
     * Create and install buildings
     ********************************************************************************************************************/
    if (enableBuildings)
    {
        std::cout << TXT_CYAN << "Installing Building" << TXT_CLEAR << std::endl;

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

        std::cout << "Installed default distribution" << std::endl;

    }

    PrintPhysicalDistributionToJson();
}

void 
TreePhysicalDistribution(ns3::NodeContainer& gnbNodes, ns3::NodeContainer& ueNodes, double mobility)
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
    // uint16_t gNbNum = 1;    // Numbers of RB
    double gNbX = 50.0;     // X position
    double gNbY = 50.0;     // Y position
    uint16_t gNbD = 80;     // Distance between gNb

    // UE Info and position
    // uint16_t ueNumPergNb = 1;   // Numbers of User per RB
    double ueDistance = .50;    //Distance between UE
    double xUE=20;  //Initial X Position UE
    double yUE=26;  //Initial Y Position UE

    // BUILDING Position
    bool enableBuildings = true; // 
    uint32_t gridWidth = 7 ; // "The number of objects laid out on a line."
    uint32_t numOfTrees = 7; 
    uint32_t nApartments = 0;
    uint32_t nFloors = 1;
    double height = 7; // Height of the trees in meters

    double buildX=37.0; // Initial X Position
    double buildY=30.0; // Initial Y Position
    double buildDx=2;  // Distance X between buildings
    double buildDy=3;  // Distance Y between buildings
    double buildLx=0.5;   // X Length
    double buildLy=0.5;   // Y Length

    // Set position of the base stations
    std::cout << TXT_CYAN << "Positioning Nodes" << TXT_CLEAR << std::endl;
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
    }

    /********************************************************************************************************************
     * Create and install buildings
     ********************************************************************************************************************/
    if (enableBuildings)
    {
        std::cout << TXT_CYAN << "Installing Building" << TXT_CLEAR << std::endl;

        Ptr<GridBuildingAllocator> gridBuildingAllocator;
        gridBuildingAllocator = CreateObject<GridBuildingAllocator>();
        gridBuildingAllocator->SetAttribute("GridWidth", UintegerValue(gridWidth)); // The number of objects laid out on a line. 1 as a column of building
        gridBuildingAllocator->SetAttribute("MinX", DoubleValue(buildX)); // The x coordinate where the grid starts.
        gridBuildingAllocator->SetAttribute("MinY", DoubleValue(buildY)); // The y coordinate where the grid starts.
        gridBuildingAllocator->SetAttribute("LengthX", DoubleValue(buildLx)); // the length of the wall of each building along the X axis.
        gridBuildingAllocator->SetAttribute("LengthY", DoubleValue(buildLy)); // the length of the wall of each building along the X axis.
        gridBuildingAllocator->SetAttribute("DeltaX", DoubleValue(buildDx)); // The x space between buildings.
        gridBuildingAllocator->SetAttribute("DeltaY", DoubleValue(buildDy)); // The y space between buildings.
        gridBuildingAllocator->SetAttribute("Height", DoubleValue(height)); // The height of the building (roof level)
        gridBuildingAllocator->SetAttribute("LayoutType", EnumValue (GridPositionAllocator::ROW_FIRST)); // The type of layout. ROW_FIRST COLUMN_FIRST

        gridBuildingAllocator->SetBuildingAttribute("NRoomsX", UintegerValue(nApartments));
        gridBuildingAllocator->SetBuildingAttribute("NRoomsY", UintegerValue(nApartments));
        gridBuildingAllocator->SetBuildingAttribute("NFloors", UintegerValue(nFloors));
        gridBuildingAllocator->SetBuildingAttribute("ExternalWallsType", EnumValue(Building::Wood));
        gridBuildingAllocator->Create(numOfTrees);

        // position of the Buildings
        Ptr<ListPositionAllocator> buildingPositionAlloc = CreateObject<ListPositionAllocator>();
        buildingPositionAlloc->Add(Vector(buildX, buildY, 0.0));
        MobilityHelper buildingmobility;
        buildingmobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
        buildingmobility.SetPositionAllocator(buildingPositionAlloc);

        BuildingsHelper::Install(gnbNodes);
        BuildingsHelper::Install(ueNodes);

        std::cout << TXT_CYAN << "Installed tree distribution." << TXT_CLEAR << std::endl;
        
    }

    PrintPhysicalDistributionToJson();
}

void 
IndoorRouterPhysicalDistribution(ns3::NodeContainer& gnbNodes, ns3::NodeContainer& ueNodes)
{
    
    double speed = 0;               // in m/s for walking UT.
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
    // uint16_t gNbNum = 1;    // Numbers of RB
    double gNbX = 50.0;     // X position
    double gNbY = 60.0;     // Y position
    uint16_t gNbD = 80;     // Distance between gNb

    // Build extra vars
    double floorHeight = 3; // Each floor height in meters
    double apartmentLenX = 6; // Apartment length (x axis) in meters
    double apartmentLenY = 5; // Apartment length (y axis) in meters

    // BUILDING Position
    bool enableBuildings = true; // 
    uint32_t gridWidth = 3 ; // "The number of objects laid out on a line."
    uint32_t numOfBuildings = 1;    // Number of buildings 
    uint32_t nApartmentsX = 3;  // Number of apartments in the X axis
    uint32_t nApartmentsY = 2;  // Number of apartments in the Y axis
    uint32_t nFloors = 10;  // Number of floors
    double buildHeight = nFloors * floorHeight; // Height of the floors in meters

    // Apartments are 30 m^2 (6,5 <-> x,y) and there are 6 per floor
    // Each floor is 3 meters tall
    // There is a total of 10 floors
    double buildX = 40.0; // Initial X Position
    double buildY = 20.0; // Initial Y Position
    double buildDx = 10;  // Distance X between buildings (Not used in IndoorRouter)
    double buildDy = 10;  // Distance Y between buildings (Not used in IndoorRouter)
    double buildLx = nApartmentsX * apartmentLenX;   // X Length
    double buildLy = nApartmentsY * apartmentLenY;   // Y Length

    // UE Info and position
    // uint16_t ueNumPergNb = 1;   // Numbers of User per RB
    double ueDistance = .50;    //Distance between UE
    // Located at Apt2, the 1.5 its so it places in the middle of the apt
    double xUE = buildX + apartmentLenX * 1.5; // Initial X Position UE
    double yUE = buildY + apartmentLenY * 2 - 1; // Initial Y Position UE
    uint8_t UEfloor = 2;  // Floor where the UE is located floor
    hUE = floorHeight * UEfloor + 1.5; // Z position of the UE (in [1, nFloors))

    // Set position of the base stations
    std::cout << TXT_CYAN << "Positioning Nodes" << TXT_CLEAR << std::endl;
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
    uemobility.Install(ueNodes);
 
    // Set Initial Position of UE
    for (uint32_t u = 0; u < ueNodes.GetN(); ++u)
    {
        std::cout << "UE: " << u << "\t" << "Pos: "<<"(" << xUE << "," << yUE +ueDistance*u <<")" << "\t" << "Speed: (" << speed << ", 0)" <<std::endl;
        ueNodes.Get(u)->GetObject<MobilityModel>()->SetPosition(Vector((float)xUE, (float) yUE +(float)ueDistance*u, hUE)); // (x, y, z) in m
        ueNodes.Get(u)->GetObject<ConstantVelocityMobilityModel>()->SetVelocity(Vector( speed, 0,  0)); // move UE1 along the x axis
    }

    /********************************************************************************************************************
     * Create and install buildings
     ********************************************************************************************************************/
    if (enableBuildings)
    {
        std::cout << TXT_CYAN << "Installing Building" << TXT_CLEAR << std::endl;

        Ptr<GridBuildingAllocator> gridBuildingAllocator;
        gridBuildingAllocator = CreateObject<GridBuildingAllocator>();
        gridBuildingAllocator->SetAttribute("GridWidth", UintegerValue(gridWidth)); // The number of objects laid out on a line. 1 as a column of building
        gridBuildingAllocator->SetAttribute("MinX", DoubleValue(buildX)); // The x coordinate where the grid starts.
        gridBuildingAllocator->SetAttribute("MinY", DoubleValue(buildY)); // The y coordinate where the grid starts.
        gridBuildingAllocator->SetAttribute("LengthX", DoubleValue(buildLx)); // the length of the wall of each building along the X axis.
        gridBuildingAllocator->SetAttribute("LengthY", DoubleValue(buildLy)); // the length of the wall of each building along the Y axis.
        gridBuildingAllocator->SetAttribute("DeltaX", DoubleValue(buildDx)); // The x space between buildings.
        gridBuildingAllocator->SetAttribute("DeltaY", DoubleValue(buildDy)); // The y space between buildings.
        gridBuildingAllocator->SetAttribute("Height", DoubleValue(buildHeight)); // The height of the building (roof level)
        gridBuildingAllocator->SetAttribute("LayoutType", EnumValue (GridPositionAllocator::ROW_FIRST)); // The type of layout. ROW_FIRST COLUMN_FIRST

        gridBuildingAllocator->SetBuildingAttribute("NRoomsX", UintegerValue(nApartmentsX));
        gridBuildingAllocator->SetBuildingAttribute("NRoomsY", UintegerValue(nApartmentsY));
        gridBuildingAllocator->SetBuildingAttribute("NFloors", UintegerValue(nFloors));
        gridBuildingAllocator->SetBuildingAttribute("ExternalWallsType", EnumValue(Building::ConcreteWithWindows));
        gridBuildingAllocator->SetBuildingAttribute("Type", EnumValue(Building::Residential));
        gridBuildingAllocator->Create(numOfBuildings);

        // position of the Buildings
        Ptr<ListPositionAllocator> buildingPositionAlloc = CreateObject<ListPositionAllocator>();
        buildingPositionAlloc->Add(Vector(buildX, buildY, 0.0));
        MobilityHelper buildingmobility;
        buildingmobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
        buildingmobility.SetPositionAllocator(buildingPositionAlloc);

        BuildingsHelper::Install(gnbNodes);
        BuildingsHelper::Install(ueNodes);

        std::cout << TXT_CYAN << "Installed IndoorRouter distribution." << TXT_CLEAR << std::endl;
        
    }

    PrintPhysicalDistributionToJson();
}