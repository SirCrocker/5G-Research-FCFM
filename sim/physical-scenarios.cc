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
PrintPhysicalDistributionToJson(NodeContainer& gnbNodes, std::string extraData)
{
    std::string predata = "{\n\"Buildings\" : [";

    std::ofstream outFile("PhysicalDistribution.json");
    if (!outFile.is_open())
    {
        NS_LOG_ERROR("Can't open file " << "PhysicalDistribution.json");
        return;
    }
    outFile << predata << std::endl;
    uint32_t index = 0;
    for (BuildingList::Iterator it = BuildingList::Begin(); it != BuildingList::End(); ++it)
    {
        ++index;
        Ptr<Building> blding = *it;
        Box box = blding->GetBoundaries();
        outFile << "\t{\n\t\t\"id\" : " << index << ", " << std::endl;
        outFile << "\t\t\"xmin\" : " << box.xMin << "," << std::endl;
        outFile << "\t\t\"xmax\" : " << box.xMax << "," << std::endl;
        outFile << "\t\t\"xwidth\" : " << box.xMax - box.xMin << "," << std::endl;
        outFile << "\t\t\"ymin\" : " << box.yMin << "," << std::endl;
        outFile << "\t\t\"ymax\" : " << box.yMax << "," << std::endl;
        outFile << "\t\t\"ywidth\" : " << box.yMax - box.yMin << "," << std::endl;
        outFile << "\t\t\"zmin\" : " << box.zMin << "," << std::endl;
        outFile << "\t\t\"zmax\" : " << box.zMax << "," << std::endl;
        outFile << "\t\t\"zwidth\" : " << box.zMax - box.zMin << "," << std::endl;
        outFile << "\t\t\"nroomsX\" : " << blding->GetNRoomsX() << "," << std::endl;
        outFile << "\t\t\"nroomsY\" : " << blding->GetNRoomsY() << "," << std::endl;
        outFile << "\t\t\"nfloors\" : " << blding->GetNFloors() << "\n\t}";
        
        if (index == BuildingList::GetNBuildings())
        {
            outFile << std::endl;
        }
        else
        {
            outFile << "," << std::endl;
        }

    }

    // Close building dict
    outFile << "]," << std::endl;

    // Start gnb dict
    outFile << "\"gnb\" : [ " << std::endl;
    for (NodeContainer::Iterator ptrNode = gnbNodes.Begin(); ptrNode != gnbNodes.End(); ++ptrNode)
    {
        Ptr<Node> node = *ptrNode;
        Vector pos = node->GetObject<MobilityModel>()->GetPosition();
        outFile << "\t{\n\t\t\"id\" : " << node->GetId() << ", " << std::endl;
        outFile << "\t\t\"x\" : " << pos.x << "," << std::endl;
        outFile << "\t\t\"y\" : " << pos.y << "," << std::endl;
        outFile << "\t\t\"z\" : " << pos.z << "\n\t}";

        if (ptrNode == --gnbNodes.End())
        {
            outFile << std::endl;
        }
        else
        {
            outFile << "," << std::endl;
        }

    }

    outFile << "],\n" << extraData << "\n}" << std::endl;
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
    double gNbX = 30.0;     // X position
    double gNbY = 50.0;     // Y position
    uint16_t gNbD = 80;     // Distance between gNb

    // UE Info and position
    // uint16_t ueNumPergNb = 1;   // Numbers of User per RB
    double ueDistance = .50;    //Distance between UE
    double xUE=10;  //Initial X Position UE
    double yUE=10;  //Initial Y Position UE

    // BUILDING Position
    bool enableBuildings = true; // 
    uint32_t gridWidth = 3 ;//
    uint32_t numOfBuildings = 2;
    uint32_t apartmentsX = 1;
    uint32_t nFloors = 10;

    double buildX=17.0; // Initial X Position
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

        std::cout << TXT_CYAN << "Installed default distribution" << TXT_CLEAR << std::endl;

    }

    PrintPhysicalDistributionToJson(gnbNodes);
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
        hBS = 20;
        hUE = 1.5;

    } else {
        NS_ABORT_MSG("Scenario not supported. Only UMa is currently supported");
    }

    // RB Info and position
    // uint16_t gNbNum = 1;    // Numbers of RB
    double gNbX = 20.0;     // X position
    double gNbY = 150.0;     // Y position
    uint16_t gNbD = 80;     // Distance between gNb

    // UE Info and position
    // uint16_t ueNumPergNb = 1;   // Numbers of User per RB
    double ueDistance = .50;    //Distance between UE
    double xUE=15;  //Initial X Position UE
    double yUE=6;  //Initial Y Position UE

    // BUILDING Position
    bool enableBuildings = true; // 
    uint32_t numOfTrees = 5*3;
    uint32_t gridWidth = numOfTrees/3 ; // "The number of objects laid out on a line."
    uint32_t nApartments = 50;
    uint32_t nFloors = 1;
    double height = 7; // Height of the trees in meters

    double buildX=10; // Initial X Position
    double buildY=15.0; // Initial Y Position
    double buildDx=4;  // Distance X between buildings
    double buildDy=40;  // Distance Y between buildings
    double buildLx=1;   // X Length
    double buildLy=1;   // Y Length

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

        // // position of the Buildings
        // Ptr<ListPositionAllocator> buildingPositionAlloc = CreateObject<ListPositionAllocator>();
        // buildingPositionAlloc->Add(Vector(buildX, buildY, 0.0));
        // MobilityHelper buildingmobility;
        // buildingmobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
        // buildingmobility.SetPositionAllocator(buildingPositionAlloc);


        uint32_t numOfTrees = 5*3;
        uint32_t gridWidth = numOfTrees/3 ; // "The number of objects laid out on a line."
        double buildX=12; // Initial X Position
        double buildY=35.0; // Initial Y Position

        Ptr<GridBuildingAllocator> gridBuildingAllocator_2;
        gridBuildingAllocator_2 = CreateObject<GridBuildingAllocator>();
        gridBuildingAllocator_2->SetAttribute("GridWidth", UintegerValue(gridWidth)); // The number of objects laid out on a line. 1 as a column of building
        gridBuildingAllocator_2->SetAttribute("MinX", DoubleValue(buildX)); // The x coordinate where the grid starts.
        gridBuildingAllocator_2->SetAttribute("MinY", DoubleValue(buildY)); // The y coordinate where the grid starts.
        gridBuildingAllocator_2->SetAttribute("LengthX", DoubleValue(buildLx)); // the length of the wall of each building along the X axis.
        gridBuildingAllocator_2->SetAttribute("LengthY", DoubleValue(buildLy)); // the length of the wall of each building along the X axis.
        gridBuildingAllocator_2->SetAttribute("DeltaX", DoubleValue(buildDx)); // The x space between buildings.
        gridBuildingAllocator_2->SetAttribute("DeltaY", DoubleValue(buildDy)); // The y space between buildings.
        gridBuildingAllocator_2->SetAttribute("Height", DoubleValue(height)); // The height of the building (roof level)
        gridBuildingAllocator_2->SetAttribute("LayoutType", EnumValue (GridPositionAllocator::ROW_FIRST)); // The type of layout. ROW_FIRST COLUMN_FIRST

        gridBuildingAllocator_2->SetBuildingAttribute("NRoomsX", UintegerValue(nApartments));
        gridBuildingAllocator_2->SetBuildingAttribute("NRoomsY", UintegerValue(nApartments));
        gridBuildingAllocator_2->SetBuildingAttribute("NFloors", UintegerValue(nFloors));
        gridBuildingAllocator_2->SetBuildingAttribute("ExternalWallsType", EnumValue(Building::Wood));
        gridBuildingAllocator_2->Create(numOfTrees);
        
        BuildingsHelper::Install(gnbNodes);
        BuildingsHelper::Install(ueNodes);

        std::cout << TXT_CYAN << "Installed Tree distribution." << TXT_CLEAR << std::endl;
    }

    PrintPhysicalDistributionToJson(gnbNodes, "\"istree\" : 1");
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
        hBS = 5.5; // https://www.subtel.gob.cl/cableado/
        hUE = 1.5;

    } else {
        NS_ABORT_MSG("Scenario not supported. Only UMa is currently supported");
    }

    // RB Info and position
    // uint16_t gNbNum = 1;    // Numbers of RB
    double gNbX = 10.0;     // X position
    double gNbY = 25.0;     // Y position
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
    double buildX = 5.0; // Initial X Position
    double buildY = 2.0; // Initial Y Position
    double buildDx = 10;  // Distance X between buildings (Not used in IndoorRouter)
    double buildDy = 10;  // Distance Y between buildings (Not used in IndoorRouter)
    double buildLx = nApartmentsX * apartmentLenX;   // X Length
    double buildLy = nApartmentsY * apartmentLenY;   // Y Length

    // UE Info and position
    // uint16_t ueNumPergNb = 1;   // Numbers of User per RB
    // double ueDistance = .50;    //Distance between UE
    // Located at Apt2, the 1.5 its so it places in the middle of the apt
    double xUE = buildX + apartmentLenX * 2.5; // Initial X Position UE
    double yUE = buildY + apartmentLenY * 1 - 1; // Initial Y Position UE
    uint8_t UEfloor = 3;  // Floor where the UE is located floor (in [1, nFloors))
    hUE = floorHeight * UEfloor + 1.5; // Z position of the UE

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
    // 2 UES first in floor 3, second on floor 8
    for (uint32_t u = 0; u < ueNodes.GetN(); ++u)
    {
        double floorForUe = u * 5 + UEfloor;
        double zUe = hUE + u * 5 * floorHeight;
        std::cout << "UE: " << u << "\t" << "Pos: "<<"(" << xUE << "," << yUE << "," << zUe << ")" << "\tFloor: " << floorForUe << "\t" << "Speed: (" << speed << ", 0)" <<std::endl;
        ueNodes.Get(u)->GetObject<MobilityModel>()->SetPosition(Vector((float)xUE, (float) yUE, zUe)); // (x, y, z) in m
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

    PrintPhysicalDistributionToJson(gnbNodes);
}
