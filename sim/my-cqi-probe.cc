/* Include ns3 libraries */
#include "ns3/applications-module.h"
#include "ns3/config-store.h"
#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/ipv4-global-routing-helper.h"
#include "ns3/log.h"
#include "ns3/mobility-module.h"
#include "ns3/network-module.h"
#include "ns3/nr-helper.h"
#include "ns3/nr-mac-scheduler-tdma-rr.h"
#include "ns3/nr-module.h"
#include "ns3/nr-point-to-point-epc-helper.h"
#include "ns3/point-to-point-helper.h"
#include <ns3/antenna-module.h>
#include <ns3/buildings-helper.h>
#include <ns3/buildings-module.h>
#include <ns3/hybrid-buildings-propagation-loss-model.h>

/* Include systems libraries */
#include <sys/types.h>
#include <unistd.h>

/* Include custom libraries (aux files for the simulation) */
#include "cmdline-colors.h"
#include "cqiprobe-apps.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("ProbeCqiSimulation");

/* Global Variables */
auto tic = std::chrono::high_resolution_clock::now();       // Initial time
auto itime = std::chrono::high_resolution_clock::now();     // Initial time 2
double simTime = 30;            // in seconds
Time timeRes = MilliSeconds(5); // Time to schedule the add noise function

/* Noise vars */
const double NOISE_MEAN = 7;    // Default value is 5
const double NOISE_VAR = 2;     // Noise variance
const double NOISE_BOUND = 3;   // Noise bound, read NormalDistribution for info about the parameter.

const double SEGMENT_SIZE = 1448.0;   // Maximum number of bits a packet can have
const std::string LOG_FILENAME = "output.log";

/* Trace functions, definitions are at EOF */
static void CwndTracer(Ptr<OutputStreamWrapper> stream, uint32_t oldval, uint32_t newval);
static void RtoTracer(Ptr<OutputStreamWrapper> stream, Time oldval, Time newval);
static void RttTracer(Ptr<OutputStreamWrapper> stream, Time oldval, Time newval);
static void NextTxTracer(Ptr<OutputStreamWrapper> stream, SequenceNumber32 old [[maybe_unused]], SequenceNumber32 nextTx);
static void NextRxTracer(Ptr<OutputStreamWrapper> stream, SequenceNumber32 old [[maybe_unused]], SequenceNumber32 nextRx);
static void InFlightTracer(Ptr<OutputStreamWrapper> stream, uint32_t old [[maybe_unused]], uint32_t inFlight);
static void SsThreshTracer(Ptr<OutputStreamWrapper> stream, uint32_t oldval, uint32_t newval);
static void TraceTcp(uint32_t nodeId, uint32_t socketId);

/* Helper functions, definitions are at EOF */
static void InstallTCP2 (Ptr<Node> remoteHost, Ptr<Node> sender, uint16_t sinkPort, float startTime, float stopTime, float dataRate);
static void CalculatePosition(NodeContainer* ueNodes, NodeContainer* gnbNodes, std::ostream* os);
static void AddRandomNoise(Ptr<NrPhy> ue_phy);


int main(int argc, char* argv[]) {
    #pragma region Variables

    double frequency = 27.3e9;      // central frequency 28e9
    double bandwidth = 100e6;       // bandwidth
    double mobility = true;         // whether to enable mobility default: false
    double speed = 1;               // in m/s for walking UT.
    bool logging = true;    // whether to enable logging from the simulation, another option is by
                            // exporting the NS_LOG environment variable
    bool shadowing = true;  // to enable shadowing effect
    bool addNoise = true;  // To enable/disable added noise to the channel

    double hBS;          // base station antenna height in meters
    double hUE;          // user antenna height in meters
    double txPower = 40; // txPower
    uint16_t numerology = 3;        // 120 kHz and 125 microseg
    std::string scenario = "UMa";   // scenario
    enum BandwidthPartInfo::Scenario scenarioEnum = BandwidthPartInfo::UMa;

    double dataRate = 100;      //Mbps
    double serverDelay = 0.01;  // remote 0.040 ; edge 0.004
    double rlcBufferPerc = 100; // x*DBP
    double rlcBuffer;           // Se calcula más abajo, según serverType

    // CQI Probe own variables.
    double cqiHighGain = 2;         // Step of CQI probe
    double ProbeCqiDuration = 200;  // miliseconds
    // double cqiGainCycle[] = {5.0 / 4, 3.0 / 4 , 1, 1, 1, 1, 1, 1}; // Similar a BBR

    // Trace activation
    bool NRTrace = true;    // whether to enable Trace NR
    bool TCPTrace = true;   // whether to enable Trace TCP

    // RB Info and position
    uint16_t gNbNum = 1;    // Numbers of RB
    uint32_t gNbSysIDbase = 1000; // gNb System ID base (every gNb starts from this)
    double gNbX = 50.0;     // X position
    double gNbY = 50.0;     // Y position
    uint16_t gNbD = 80;     // Distance between gNb

    // UE Info and position
    uint16_t ueNumPergNb = 1;   // Numbers of User per RB
    uint32_t ueSysIDbase = 2000; // UE System ID base (every UE starts from this)
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

    std::string serverType = "Remote";  // Transport Protocol
    std::string flowType = "UDP";       // Transport Protocol
    std::string tcpTypeId = "TcpBbr";   // TCP Type
    double AppStartTime = 0.2;          // APP start time

    #pragma endregion Variables

    /* Simulation arguments */
    #pragma region SimArguments

    CommandLine cmd(__FILE__);
    cmd.AddValue("frequency", "The central carrier frequency in Hz.", frequency);
    cmd.AddValue("mobility",
                 "If set to 1 UEs will be mobile, when set to 0 UE will be static. By default, "
                 "they are mobile.",
                 mobility);
    cmd.AddValue("logging", "If set to 0, log components will be disabled.", logging);
    cmd.AddValue("simTime", "Simulation Time (s)", simTime);
    cmd.AddValue("bandwidth", "bandwidth in Hz.", bandwidth);
    cmd.AddValue("serverType", "Type of Server: Remote or Edge", serverType);
    cmd.AddValue("flowType", "Flow Type: UDP or TCP", flowType);
    cmd.AddValue("rlcBufferPerc", "Percent RLC Buffer", rlcBufferPerc);
    cmd.AddValue("tcpTypeId", "TCP flavor: TcpBbr , TcpNewReno, TcpCubic, TcpVegas, TcpIllinois, TcpYeah, TcpHighSpeed, TcpBic", tcpTypeId);
    cmd.AddValue("enableBuildings", "If set to 1, enable Buildings", enableBuildings);
    cmd.AddValue("shadowing", "If set to 1, enable Shadowing", shadowing);
    cmd.AddValue("cqiHighGain", "Steps of CQI Probe. Means CQI=round(CQI*cqiHighGain)", cqiHighGain);
    cmd.AddValue("addNoise", "Add normal distributed noise to the simulation", addNoise);

    cmd.Parse(argc, argv);

    #pragma endregion SimArguments
    
    /********************************************************************************************************************
     * LOGS
    ********************************************************************************************************************/
    #pragma region logs
    // Redirect logs to output file, clog -> LOG_FILENAME
    std::ofstream of(LOG_FILENAME);
    auto clog_buff = std::clog.rdbuf();
    std::clog.rdbuf(of.rdbuf());

    // enable logging
    if (logging)
    {
        // LogComponentEnable ("LteRlcUm", LOG_LEVEL_ALL);
        // LogComponentEnable ("ThreeGppSpectrumPropagationLossModel", LOG_LEVEL_ALL);
        // LogComponentEnable("ThreeGppPropagationLossModel", LOG_LEVEL_ALL);
        // LogComponentEnable ("ThreeGppChannelModel", LOG_LEVEL_ALL);
        // LogComponentEnable ("ChannelConditionModel", LOG_LEVEL_ALL);
        // LogComponentEnable("TcpCongestionOps",LOG_LEVEL_ALL);
        // LogComponentEnable("TcpBic",LOG_LEVEL_ALL);
        // LogComponentEnable("TcpBbr",LOG_LEVEL_ALL);
        // LogComponentEnable ("UdpClient", LOG_LEVEL_INFO);
        // LogComponentEnable ("UdpServer", LOG_LEVEL_INFO);
        // LogComponentEnable ("LteRlcUm", LOG_LEVEL_LOGIC);
        // LogComponentEnable ("LtePdcp", LOG_LEVEL_INFO);
        // LogComponentEnable("NrUePhy", LOG_ALL);
    }

    #pragma endregion logs

    /********************************************************************************************************************
     * Servertype, TCP config & settings, scenario definition
    ********************************************************************************************************************/
    #pragma region sv_tcp_scenario

    if (serverType == "Remote")
    {
        serverDelay = 0.04; 
    }
    else
    {
        serverDelay = 0.004;
    }
    rlcBuffer = round(dataRate*1e6/8*serverDelay*rlcBufferPerc/100); // Bytes BDP=250Mbps*100ms default: 999999999

    // TCP config
    // TCP Setting
    // attibutes in: https://www.nsnam.org/docs/release/3.27/doxygen/classns3_1_1_tcp_socket.html
    uint32_t delAckCount = 1;
    std::string queueDisc = "FifoQueueDisc";
    queueDisc = std::string("ns3::") + queueDisc;

    if (flowType =="TCP"){
        Config::SetDefault("ns3::TcpL4Protocol::SocketType", StringValue("ns3::" + tcpTypeId));
        Config::SetDefault("ns3::TcpSocket::SndBufSize", UintegerValue(4194304)); // TcpSocket maximum transmit buffer size (bytes). 4194304 = 4MB
        Config::SetDefault("ns3::TcpSocket::RcvBufSize", UintegerValue(4194304)); // TcpSocket maximum receive buffer size (bytes). 6291456 = 6MB
        Config::SetDefault("ns3::TcpSocket::InitialCwnd", UintegerValue(10)); // TCP initial congestion window size (segments). RFC 5681 = 10
        Config::SetDefault("ns3::TcpSocket::SegmentSize", UintegerValue(SEGMENT_SIZE)); // TCP maximum segment size in bytes (may be adjusted based on MTU discovery).
        Config::SetDefault("ns3::TcpSocket::TcpNoDelay", BooleanValue(false)); // Set to true to disable Nagle's algorithm


        // Config::SetDefault("ns3::TcpSocketBase::MinRto", TimeValue (MilliSeconds (200)));
        Config::SetDefault("ns3::TcpSocket::DelAckCount", UintegerValue(delAckCount));  // Number of packets to wait before sending a TCP ack
        Config::SetDefault("ns3::TcpSocket::DelAckTimeout", TimeValue (Seconds (.4))); // Timeout value for TCP delayed acks, in seconds. default 0.2 sec
        Config::SetDefault("ns3::TcpSocket::DataRetries", UintegerValue(100)); // Number of data retransmission attempts. Default 6
        Config::SetDefault("ns3::TcpSocket::PersistTimeout", TimeValue (Seconds (10))); // Number of data retransmission attempts. Default 6

        Config::Set ("/NodeList/*/DeviceList/*/TxQueue/MaxSize",  QueueSizeValue(QueueSize ("100p")));
        Config::Set ("/NodeList/*/DeviceList/*/RxQueue/MaxSize",  QueueSizeValue(QueueSize ("100p")));
        Config::SetDefault("ns3::DropTailQueue<Packet>::MaxSize", QueueSizeValue(QueueSize ("100p"))); //A FIFO packet queue that drops tail-end packets on overflow
        Config::SetDefault(queueDisc + "::MaxSize", QueueSizeValue(QueueSize("100p"))); //100p Simple queue disc implementing the FIFO (First-In First-Out) policy
        Config::SetDefault("ns3::TcpL4Protocol::RecoveryType",
                           TypeIdValue(TypeId::LookupByName("ns3::TcpClassicRecovery"))); //set the congestion window value to the slow start threshold and maintain it at such value until we are fully recovered
        Config::SetDefault ("ns3::RttEstimator::InitialEstimation", TimeValue (MilliSeconds (10)));

        if( tcpTypeId=="TcpCubic"){
            Config::SetDefault("ns3::TcpCubic::Beta", DoubleValue(1)); // Beta for multiplicative decrease. Default 0.7
  
        }
        else if( tcpTypeId=="TcpBic"){
            Config::SetDefault("ns3::TcpBic::Beta", DoubleValue(1.5)); // Beta for multiplicative decrease. Default 0.8
            Config::SetDefault("ns3::TcpBic::HyStart", BooleanValue(false)); // Enable (true) or disable (false) hybrid slow start algorithm. Default true
            
        }

    }
    else{
        // TCPTrace=false;
    }

    /**
     * Default values for the simulation. We are progressively removing all
     * the instances of SetDefault, but we need it for legacy code (LTE)
     */
    Config::SetDefault("ns3::LteRlcUm::MaxTxBufferSize", UintegerValue(rlcBuffer));

    // set mobile device and base station antenna heights in meters, according to the chosen
    // scenario
    if (scenario == "UMa")
    {
        hBS = 25;
        hUE = 1.5;
        if (enableBuildings)
        {
            scenarioEnum = BandwidthPartInfo::UMa_Buildings;
        }
        else{
            scenarioEnum = BandwidthPartInfo::UMa;
        }

    
    }
    else
    {
        NS_ABORT_MSG("Scenario not supported. Choose among 'RMa', 'UMa', 'UMi-StreetCanyon', "
                     "'InH-OfficeMixed', and 'InH-OfficeOpen'.");
    }
    
    #pragma endregion sv_tcp_scenario

    /********************************************************************************************************************
    * Create base stations and mobile terminal
    * Define positions, mobility types and speed of UE and gNB.
    ********************************************************************************************************************/
    #pragma region UE_gNB   

    NodeContainer gnbNodes;
    NodeContainer ueNodes;
    gnbNodes.Create(gNbNum, gNbSysIDbase);
    ueNodes.Create(gNbNum*ueNumPergNb, ueSysIDbase);

    // Set position of the base stations
    std::cout << cyan << "Positioning Nodes" << clear << std::endl;
    Ptr<ListPositionAllocator> enbPositionAlloc = CreateObject<ListPositionAllocator>();
    for (uint32_t u = 0; u < gnbNodes.GetN(); ++u)
    {
        std::cout << "Node ID " << gnbNodes.Get (u)->GetId() << " Sys ID:" << gnbNodes.Get(u)->GetSystemId() + u << std::endl;
        std::cout << "gNb: " << u << "\t" << "(" << gNbX << "," << gNbY+gNbD*u <<")" << std::endl;
        enbPositionAlloc->Add(Vector(gNbX, gNbY+gNbD*u, hBS));
    }
    MobilityHelper enbmobility;
    enbmobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    enbmobility.SetPositionAllocator(enbPositionAlloc);
    enbmobility.Install(gnbNodes);

    // position the mobile terminals and enable the mobility
    MobilityHelper uemobility;
    uemobility.SetMobilityModel("ns3::ConstantVelocityMobilityModel");
    // uemobility.SetMobilityModel("ns3::RandomDirection2dMobilityModel","Bounds", RectangleValue(Rectangle(x_min, x_max, y_min, y_max)));
    // uemobility.SetMobilityModel("ns3::WaypointMobilityModel");
    uemobility.Install(ueNodes);


    if (mobility==false){
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

    }

    /********************************************************************************************************************
     * NR Stuff
     ********************************************************************************************************************/
    #pragma region NR_Config
    /**
     * Create NR simulation helpers
     */
    Ptr<NrPointToPointEpcHelper> epcHelper = CreateObject<NrPointToPointEpcHelper>();
    Ptr<IdealBeamformingHelper> idealBeamformingHelper = CreateObject<IdealBeamformingHelper>();

    Ptr<NrHelper> nrHelper = CreateObject<NrHelper>();
    nrHelper->SetBeamformingHelper(idealBeamformingHelper);
    nrHelper->SetEpcHelper(epcHelper);
    
    /**
     * Spectrum configuration. We create a single operational band and configure the scenario.
     */
    BandwidthPartInfoPtrVector allBwps;
    CcBwpCreator ccBwpCreator;
    const uint8_t numCcPerBand = 1; // in this example we have a single band, and that band is
                                    // composed of a single component carrier

    /** Create the configuration for the CcBwpHelper. SimpleOperationBandConf creates
     * a single BWP per CC and a single BWP in CC.
     *
     * Hence, the configured spectrum is:
     *
     * |---------------Band---------------|
     * |---------------CC-----------------|
     * |---------------BWP----------------|
     */
    CcBwpCreator::SimpleOperationBandConf bandConf(frequency,
                                                   bandwidth,
                                                   numCcPerBand,
                                                   scenarioEnum);
    OperationBandInfo band = ccBwpCreator.CreateOperationBandContiguousCc(bandConf);

     // Initialize channel and pathloss, plus other things inside band.
     
    Config::SetDefault("ns3::ThreeGppChannelModel::UpdatePeriod", TimeValue(MilliSeconds(0)));
    std::string errorModel = "ns3::NrEesmIrT1"; //ns3::NrEesmCcT1, ns3::NrEesmCcT2, ns3::NrEesmIrT1, ns3::NrEesmIrT2, ns3::NrLteMiErrorModel
    Config::SetDefault("ns3::NrAmc::ErrorModelType", TypeIdValue(TypeId::LookupByName(errorModel)));
    Config::SetDefault("ns3::NrAmc::AmcModel", EnumValue(NrAmc::ErrorModel)); // NrAmc::ShannonModel // NrAmc::ErrorModel
    //we need activate? : "ns3::BuildingsChannelConditionModel"

    std::string pathlossModel="ns3::ThreeGppUmaPropagationLossModel";

    nrHelper->SetChannelConditionModelAttribute("UpdatePeriod", TimeValue(MilliSeconds(0)));
    nrHelper->SetPathlossAttribute("ShadowingEnabled", BooleanValue(shadowing)); // false: allow see effect of path loss only

    Ptr<HybridBuildingsPropagationLossModel> propagationLossModel =
        CreateObject<HybridBuildingsPropagationLossModel>();
    // cancel shadowing effect set 0.0
    propagationLossModel->SetAttribute("ShadowSigmaOutdoor", DoubleValue(7.0)); // Standard deviation of the normal distribution used for calculate the shadowing for outdoor nodes
    propagationLossModel->SetAttribute("ShadowSigmaIndoor", DoubleValue(8.0)); // Standard deviation of the normal distribution used for calculate the shadowing for indoor nodes
    propagationLossModel->SetAttribute("ShadowSigmaExtWalls", DoubleValue(5.0)); // Standard deviation of the normal distribution used for calculate the shadowing due to ext walls
    propagationLossModel->SetAttribute("InternalWallLoss", DoubleValue(5.7)); // Additional loss for each internal wall [dB]


    // Initialize channel and pathloss, plus other things inside band.
    nrHelper->InitializeOperationBand(&band);
    allBwps = CcBwpCreator::GetAllBwps({band});

    // Configure ideal beamforming method
    idealBeamformingHelper->SetAttribute("BeamformingMethod",
                                         TypeIdValue(DirectPathBeamforming::GetTypeId()));// dir at gNB, dir at UE

    // Configure scheduler
    nrHelper->SetSchedulerTypeId(NrMacSchedulerTdmaRR::GetTypeId());


    // Antennas for the UEs
    nrHelper->SetUeAntennaAttribute("NumRows", UintegerValue(2));
    nrHelper->SetUeAntennaAttribute("NumColumns", UintegerValue(4));
    nrHelper->SetUeAntennaAttribute("AntennaElement",
                                    PointerValue(CreateObject<IsotropicAntennaModel>()));
    
    // Antennas for the gNbs
    nrHelper->SetGnbAntennaAttribute("NumRows", UintegerValue(8));
    nrHelper->SetGnbAntennaAttribute("NumColumns", UintegerValue(8));
    nrHelper->SetGnbAntennaAttribute("AntennaElement",
                                     PointerValue(CreateObject<IsotropicAntennaModel>()));

    // install nr net devices
    NetDeviceContainer enbNetDev = nrHelper->InstallGnbDevice(gnbNodes, allBwps);
    NetDeviceContainer ueNetDev = nrHelper->InstallUeDevice(ueNodes, allBwps);

    int64_t randomStream = 1;
    randomStream += nrHelper->AssignStreams(enbNetDev, randomStream);
    randomStream += nrHelper->AssignStreams(ueNetDev, randomStream);

    for (uint32_t u = 0; u < gnbNodes.GetN(); ++u)
    {
        nrHelper->GetGnbPhy(enbNetDev.Get(u), 0)->SetTxPower(txPower);
        nrHelper->GetGnbPhy(enbNetDev.Get(u), 0)
            ->SetAttribute("Numerology", UintegerValue(numerology));
    }

    if (addNoise) 
    {   
        // Get the physical layer and add noise whenerver DlDataSinr is executed
        Ptr<NrUePhy> uePhy = nrHelper->GetUePhy(ueNetDev.Get(0), 0);

        uePhy->SetNoiseFigure(NOISE_MEAN);

        for (int i = 0; i < Seconds(simTime) / timeRes; i++)
        {
            Simulator::Schedule(timeRes * i, &AddRandomNoise, uePhy);
        }

        // Config::ConnectWithoutContext("/NodeList/*/DeviceList/*/ComponentCarrierMapUe/*/NrUePhy/DlDataSinr",
        //                MakeBoundCallback(&AddRandomNoise, uePhy));
    }

    // When all the configuration is done, explicitly call UpdateConfig ()
    for (auto it = enbNetDev.Begin(); it != enbNetDev.End(); ++it)
    {
        DynamicCast<NrGnbNetDevice>(*it)->UpdateConfig();
    }

    for (auto it = ueNetDev.Begin(); it != ueNetDev.End(); ++it)
    {
        DynamicCast<NrUeNetDevice>(*it)->UpdateConfig();
    }
    #pragma endregion NR_Config

    /********************************************************************************************************************
     * Setup and install IP, internet and remote servers
     ********************************************************************************************************************/
    #pragma region internet
    // create the internet and install the IP stack on the UEs
    // get SGW/PGW and create a single RemoteHost
    Ptr<Node> pgw = epcHelper->GetPgwNode();
    NodeContainer remoteHostContainer;
    remoteHostContainer.Create(1);
    Ptr<Node> remoteHost = remoteHostContainer.Get(0);
    InternetStackHelper internet;
    internet.Install(remoteHostContainer);

    // connect a remoteHost to pgw. Setup routing too
    PointToPointHelper p2ph;
    p2ph.SetDeviceAttribute("DataRate", DataRateValue(DataRate("100Gb/s")));
    p2ph.SetDeviceAttribute("Mtu", UintegerValue(1500)); //2500
    p2ph.SetChannelAttribute("Delay", TimeValue(Seconds(serverDelay)));
    NetDeviceContainer internetDevices = p2ph.Install(pgw, remoteHost);

    Ipv4AddressHelper ipv4h;
    ipv4h.SetBase("1.0.0.0", "255.0.0.0");
    Ipv4InterfaceContainer internetIpIfaces = ipv4h.Assign(internetDevices);
    Ipv4StaticRoutingHelper ipv4RoutingHelper;

    Ptr<Ipv4StaticRouting> remoteHostStaticRouting =
        ipv4RoutingHelper.GetStaticRouting(remoteHost->GetObject<Ipv4>());
    remoteHostStaticRouting->AddNetworkRouteTo(Ipv4Address("7.0.0.0"), Ipv4Mask("255.0.0.0"), 1);
    internet.Install(ueNodes);

    Ipv4InterfaceContainer ueIpIface;
    ueIpIface = epcHelper->AssignUeIpv4Address(NetDeviceContainer(ueNetDev));

    // attach UEs to the closest eNB
    nrHelper->AttachToClosestEnb(ueNetDev, enbNetDev);

    // assign IP address to UEs
    for (uint32_t u = 0; u < ueNodes.GetN(); ++u)
    {
        Ptr<Node> ueNode = ueNodes.Get(u);
        // Set the default gateway for the UE
        Ptr<Ipv4StaticRouting> ueStaticRouting =
            ipv4RoutingHelper.GetStaticRouting(ueNode->GetObject<Ipv4>());
        ueStaticRouting->SetDefaultRoute(epcHelper->GetUeDefaultGatewayAddress(), 1);
    }


    if ( flowType == "UDP")
    {
        std::cout << "App:" << flowType << std::endl;
        uint16_t dlPort = 1234;
        double interval = SEGMENT_SIZE*8/dataRate; // MicroSeconds
        // install downlink applications
        ApplicationContainer clientApps;
        ApplicationContainer serverApps;

        for (uint32_t u = 0; u < ueNodes.GetN(); ++u)
        {
            UdpServerHelper dlPacketSinkHelper(dlPort);
            serverApps.Add(dlPacketSinkHelper.Install(ueNodes.Get(u)));

            UdpClientHelper dlClient(ueIpIface.GetAddress(u), dlPort);
            dlClient.SetAttribute("Interval", TimeValue(MicroSeconds(interval)));
            dlClient.SetAttribute("MaxPackets", UintegerValue(0xFFFFFFFF));
            dlClient.SetAttribute("PacketSize", UintegerValue(SEGMENT_SIZE));
            clientApps.Add(dlClient.Install(remoteHost));
        }
        // start server and client apps
        serverApps.Start(Seconds(AppStartTime));
        clientApps.Start(Seconds(AppStartTime));
        serverApps.Stop(Seconds(simTime));
        clientApps.Stop(Seconds(simTime - AppStartTime));
    }
    else if ( flowType == "TCP")
    {

        std::cout << cyan << "Install App: " << flowType << " " << tcpTypeId << clear << std::endl;
        uint16_t sinkPort = 8080;

        for (uint32_t u = 0; u < ueNodes.GetN(); ++u)
        {
            //firstRto[u + 1] = true;
            auto start = AppStartTime + 0.01 * u;
            auto end = std::max (start + 1., simTime - start);

            // InstallTCP (remoteHostContainer.Get (0), ueNodes.Get (u), sinkPort++, start, end);
            InstallTCP2 (remoteHostContainer.Get (0), ueNodes.Get (u), sinkPort++, start, end, dataRate);

            std::cout << cyan << 
                    "Install TCP between nodes: " << std::to_string(remoteHostContainer.Get (0)->GetId()) << "<->"<< std::to_string(ueNodes.Get (u)->GetId()) <<
                    clear << std::endl;

            // Hook TRACE SOURCE after application starts
            // this work because u is identical to socketid i this case
            Simulator::Schedule(Seconds(AppStartTime + 0.01 *ueNodes.GetN()) , 
                                &TraceTcp, remoteHostContainer.Get (0)->GetId(), u);

          
        }
    }
    #pragma endregion internet

    /********************************************************************************************************************
     * Trace and file generation
     ********************************************************************************************************************/
    #pragma region trace_n_files
    // enable the traces provided by the nr module
    if (NRTrace)
    {
        nrHelper->EnableTraces();
    }

    // All tcp trace
    if(TCPTrace){
        std::ofstream asciiTCP;
        Ptr<OutputStreamWrapper> ascii_wrap;
        asciiTCP.open("tcp-all-ascii.txt");
        ascii_wrap = new OutputStreamWrapper("tcp-all-ascii.txt", std::ios::out);
        internet.EnableAsciiIpv4All(ascii_wrap);
    }


    // Calculate the node positions
    std::string logMFile="mobilityPosition.txt";
    std::ofstream mymcf;
    mymcf.open(logMFile);
    mymcf  << "Time\t" << "UE\t" << "x\t" << "y\t"  << "D0" << std::endl;
    Simulator::Schedule(MilliSeconds(100), &CalculatePosition, &ueNodes, &gnbNodes, &mymcf);

    // 
    // generate graph.ini
    //
    std::string iniFile="graph.ini";
    std::ofstream inif;
    inif.open(iniFile);
    inif << "[general]" << std::endl;
    inif << "resamplePeriod = 100" << std::endl;
    inif << "simTime = " << simTime << std::endl;
    inif << "AppStartTime = " << AppStartTime << std::endl;
    inif << "NRTrace = " << NRTrace << std::endl;
    inif << "TCPTrace = " << TCPTrace << std::endl;
    inif << "flowType = " << flowType << std::endl;
    inif << "tcpTypeId = " << tcpTypeId << std::endl;
    inif << "frequency = " << frequency << std::endl;
    inif << "bandwidth = " << bandwidth << std::endl;
    inif << "serverID = " << (int)(ueNumPergNb+gNbNum+3) << std::endl;
    inif << "UENum = " << (int)(ueNumPergNb) << std::endl;
    inif << "SegmentSize = " << SEGMENT_SIZE << std::endl;
    inif << "rlcBuffer = " << rlcBuffer << std::endl;
    inif << "rlcBufferPerc = " << rlcBufferPerc << std::endl;
    inif << "serverType = " << serverType << std::endl;
    inif << "dataRate = " << dataRate << std::endl;
    inif << "cqiHighGain = " << cqiHighGain << std::endl;
    inif << "ProbeCqiDuration = " << ProbeCqiDuration << std::endl;
    inif << "addNoise = " << addNoise << std::endl;

    inif << std::endl;
    inif << "[gNb]" << std::endl;
    inif << "gNbNum = " << gNbNum << std::endl;
    inif << "gNbX = "   << gNbX   << std::endl;
    inif << "gNbY = "   << gNbY   << std::endl;
    inif << "gNbD = "   << gNbD   << std::endl;

    inif << std::endl;
    inif << "[building]" << std::endl;
    inif << "enableBuildings = " << enableBuildings << std::endl;
    inif << "gridWidth = " << gridWidth << std::endl;
    inif << "buildN = " << numOfBuildings << std::endl;
    inif << "buildX = " << buildX << std::endl;
    inif << "buildY = " << buildY << std::endl;
    inif << "buildDx = " << buildDx << std::endl;
    inif << "buildDy = " << buildDy << std::endl;
    inif << "buildLx = " << buildLx << std::endl;
    inif << "buildLy = " << buildLy << std::endl;
    inif.close();

    #pragma endregion trace_n_files

    Simulator::Stop(Seconds(simTime));
    Simulator::Run();
    Simulator::Destroy();

    std::clog.rdbuf(clog_buff); // Redirect clog to original buffer

    std::cout << "\nThe End" << std::endl;
    auto toc = std::chrono::high_resolution_clock::now();
    std::cout << "Total Time: " << "\033[1;35m"  << 1.e-9*std::chrono::duration_cast<std::chrono::nanoseconds>(toc-itime).count() << "\033[0m"<<  std::endl;

    return 0;
};

/********************************************************************************************************************
 * Trace and util functions (Own)
********************************************************************************************************************/
#pragma region trace_n_utils_functions
/**
 * CWND tracer.
 *
 * \param context The context.
 * \param oldval Old value.
 * \param newval New value.
 */
static void
CwndTracer(Ptr<OutputStreamWrapper> stream, uint32_t oldval, uint32_t newval)
{
    //*stream->GetStream() << Simulator::Now().GetSeconds() << " " << newval / SegmentSize << std::endl;
    *stream->GetStream() << Simulator::Now().GetSeconds() << "\t" << oldval  << "\t" << newval  << std::endl;
}

/**
 * RTO tracer.
 *
 * \param context The context.
 * \param oldval Old value.
 * \param newval New value.
 */
static void
RtoTracer(Ptr<OutputStreamWrapper> stream, Time oldval, Time newval)
{
    *stream->GetStream()  << Simulator::Now().GetSeconds() << "\t" << (float) oldval.GetSeconds()<< "\t" << (float) newval.GetSeconds() << std::endl;
}

/**
 * RTT tracer.
 *
 * \param context The context.
 * \param oldval Old value.
 * \param newval New value.
 */
static void
RttTracer(Ptr<OutputStreamWrapper> stream, Time oldval, Time newval)
{
    *stream->GetStream()  << Simulator::Now().GetSeconds() << "\t" << (float) oldval.GetSeconds()<< "\t" << (float) newval.GetSeconds() << std::endl;

}

/**
 * Next TX tracer.
 *
 * \param context The context.
 * \param old Old sequence number.
 * \param nextTx Next sequence number.
 */
static void
NextTxTracer(Ptr<OutputStreamWrapper> stream, SequenceNumber32 old [[maybe_unused]], SequenceNumber32 nextTx)
{
    *stream->GetStream() << Simulator::Now().GetSeconds() << "\t" << old<< "\t" << nextTx << std::endl;
}

/**
 * Next RX tracer.
 *
 * \param context The context.
 * \param old Old sequence number.
 * \param nextRx Next sequence number.
 */
static void
NextRxTracer(Ptr<OutputStreamWrapper> stream, SequenceNumber32 old [[maybe_unused]], SequenceNumber32 nextRx)
{
    *stream->GetStream()  << Simulator::Now().GetSeconds() << "\t" << old<< "\t" << nextRx << std::endl;
}

/**
 * In-flight tracer.
 *
 * \param context The context.
 * \param old Old value.
 * \param inFlight In flight value.
 */
static void
InFlightTracer(Ptr<OutputStreamWrapper> stream, uint32_t old [[maybe_unused]], uint32_t inFlight)
{
    *stream->GetStream()  << Simulator::Now().GetSeconds() << "\t" << old<< "\t" << inFlight << std::endl;
}

/**
 * Slow start threshold tracer.
 *
 * \param context The context.
 * \param oldval Old value.
 * \param newval New value.
 */
static void
SsThreshTracer(Ptr<OutputStreamWrapper> stream, uint32_t oldval, uint32_t newval)
{
    *stream->GetStream()  << Simulator::Now().GetSeconds() << "\t" << oldval<< "\t" << newval << std::endl;
}

/**
* Función para imprimir en pantalla info del nodo y el socket, luego guarda en archivos txt info pertinente a TCP L4.
* Guarda:
*   - CWND
*   - RTO
*   - RTT
*   - NextTxSequence
*   - NextRxSequence
*   - BytesInFlight
*   - SS Threshold
*/
static void
TraceTcp(uint32_t nodeId, uint32_t socketId)
{
    std::cout << "\r\e[K" << cyan << "Trace TCP: " << nodeId << "<->" << socketId << " at: "<<  
            1.e-9*std::chrono::duration_cast<std::chrono::nanoseconds>(tic-itime).count()<< clear << std::endl;


    // Init Congestion Window Tracer
    AsciiTraceHelper asciicwnd;
    Ptr<OutputStreamWrapper> stream = asciicwnd.CreateFileStream( "tcp-cwnd-"
                                    + std::to_string(nodeId) +"-"+std::to_string(socketId)+".txt");
    *stream->GetStream() << "Time" << "\t" << "oldval" << "\t" << "newval" << std::endl;

    Config::ConnectWithoutContext("/NodeList/" + std::to_string(nodeId) +
                                    "/$ns3::TcpL4Protocol/SocketList/" +
                                    std::to_string(socketId) + "/CongestionWindow",
                                    MakeBoundCallback(&CwndTracer, stream));

    // Init Congestion RTO
    AsciiTraceHelper asciirto;
    Ptr<OutputStreamWrapper> rtoStream = asciirto.CreateFileStream("tcp-rto-"
                                    + std::to_string(nodeId) +"-"+std::to_string(socketId)+".txt");
    *rtoStream->GetStream() << "Time" << "\t" << "oldval" << "\t" << "newval" << std::endl;
    Config::ConnectWithoutContext("/NodeList/" + std::to_string(nodeId) +
                                    "/$ns3::TcpL4Protocol/SocketList/" +
                                    std::to_string(socketId) + "/RTO",
                                    MakeBoundCallback(&RtoTracer,rtoStream));

    // Init Congestion RTT
    AsciiTraceHelper asciirtt;
    Ptr<OutputStreamWrapper> rttStream = asciirtt.CreateFileStream("tcp-rtt-"
                                    + std::to_string(nodeId) +"-"+std::to_string(socketId)+".txt");
    *rttStream->GetStream() << "Time" << "\t" << "oldval" << "\t" << "newval" << std::endl;
    Config::ConnectWithoutContext("/NodeList/" + std::to_string(nodeId) +
                                    "/$ns3::TcpL4Protocol/SocketList/" +
                                    std::to_string(socketId) + "/RTT",
                                    MakeBoundCallback(&RttTracer,rttStream));

    // Init Congestion NextTxTracer
    AsciiTraceHelper asciinexttx;
    Ptr<OutputStreamWrapper> nexttxStream = asciinexttx.CreateFileStream("tcp-nexttx-"
                                    + std::to_string(nodeId) +"-"+std::to_string(socketId)+".txt");
    *nexttxStream->GetStream() << "Time" << "\t" << "oldval" << "\t" << "newval" << std::endl;
    Config::ConnectWithoutContext("/NodeList/" + std::to_string(nodeId) +
                                    "/$ns3::TcpL4Protocol/SocketList/" +
                                    std::to_string(socketId) + "/NextTxSequence",
                                    MakeBoundCallback(&NextTxTracer,nexttxStream));

    // Init Congestion NextRxTracer
    AsciiTraceHelper asciinextrx;
    Ptr<OutputStreamWrapper> nextrxStream = asciinextrx.CreateFileStream("tcp-nextrx-"
                                    + std::to_string(nodeId) +"-"+std::to_string(socketId)+".txt");
    *nextrxStream->GetStream() << "Time" << "\t" << "oldval" << "\t" << "newval" << std::endl;
    Config::ConnectWithoutContext("/NodeList/" + std::to_string(nodeId) +
                                    "/$ns3::TcpL4Protocol/SocketList/" +
                                    std::to_string(socketId) + "/RxBuffer/NextRxSequence",
                                    MakeBoundCallback(&NextRxTracer,nextrxStream));

                                    
    // Init Congestion InFlightTracer
    AsciiTraceHelper asciiinflight;
    Ptr<OutputStreamWrapper> inflightStream = asciiinflight.CreateFileStream("tcp-inflight-"
                                    + std::to_string(nodeId) +"-"+std::to_string(socketId)+".txt");
    *inflightStream->GetStream() << "Time" << "\t" << "oldval" << "\t" << "newval" << std::endl;
    Config::ConnectWithoutContext("/NodeList/" + std::to_string(nodeId) +
                                    "/$ns3::TcpL4Protocol/SocketList/" +
                                    std::to_string(socketId) + "/BytesInFlight",
                                    MakeBoundCallback(&InFlightTracer,inflightStream));

    // Init Congestion SsThreshTracer
    AsciiTraceHelper asciissth;
    Ptr<OutputStreamWrapper> ssthStream = asciissth.CreateFileStream("tcp-ssth-"
                                    + std::to_string(nodeId) +"-"+std::to_string(socketId)+".txt");
    *ssthStream->GetStream() << "Time" << "\t" << "oldval" << "\t" << "newval" << std::endl;
    Config::ConnectWithoutContext("/NodeList/" + std::to_string(nodeId) +
                                    "/$ns3::TcpL4Protocol/SocketList/" +
                                    std::to_string(socketId) + "/SlowStartThreshold",
                                    MakeBoundCallback(&SsThreshTracer,ssthStream));

}

/**
 * InstallTCP2
 * Instala la aplicaciión "MyApp" en los nodos remoteHost, sender.
 */
static void InstallTCP2 (Ptr<Node> remoteHost,
                        Ptr<Node> sender,
                        uint16_t sinkPort,
                        float startTime,
                        float stopTime, float dataRate)
{
    //Address sinkAddress (InetSocketAddress (ueIpIface.GetAddress (0), sinkPort));
    Address sinkAddress (InetSocketAddress (sender->GetObject<Ipv4> ()->GetAddress (1,0).GetLocal (), sinkPort));
    PacketSinkHelper packetSinkHelper ("ns3::TcpSocketFactory", InetSocketAddress (Ipv4Address::GetAny (), sinkPort));
    ApplicationContainer sinkApps = packetSinkHelper.Install (sender);

    sinkApps.Start (Seconds (0.));
    sinkApps.Stop (Seconds (simTime));

    Ptr<Socket> ns3TcpSocket = Socket::CreateSocket (remoteHost, TcpSocketFactory::GetTypeId ());
    Ptr<MyApp> app = CreateObject<MyApp> ();
    app->Setup (ns3TcpSocket, sinkAddress, SEGMENT_SIZE, 0xFFFFFFFF, DataRate (std::to_string(dataRate) + "Mb/s"));

    remoteHost->AddApplication (app);


    app->SetStartTime (Seconds (startTime));
    app->SetStopTime (Seconds (stopTime));
    
}

/**
 * Calulate the Position
 * Imprime info en la consola
 */
static void
CalculatePosition(NodeContainer* ueNodes, NodeContainer* gnbNodes, std::ostream* os)
{
    auto toc = std::chrono::high_resolution_clock::now();
    Time now = Simulator::Now(); 
    pid_t pid = getpid();
    auto elapsed_time = 1.e-9*std::chrono::duration_cast<std::chrono::nanoseconds>(toc-itime).count();

    std::cout << "\r\e[K" << "pid: " << green << pid << clear << 
            " ST: " << "\033[1;32m["  << now.GetSeconds() << "/"<< simTime <<"] "<< "\033[0m"<<  
            " PT: " << 1.e-9*std::chrono::duration_cast<std::chrono::nanoseconds>(toc-tic).count()<< " "
            " ET: " << "\033[1;35m"  << elapsed_time << "\033[0m"<< " " <<
            " RT: " << "\033[1;34m"  << elapsed_time * (simTime / now.GetSeconds() - 1) << "\033[0m"<< std::flush;
    // std::cout << "SimTime: "<<now.GetSeconds() << "/"<< simTime <<"\t"<<  "Processed in: " << 1.e-9*std::chrono::duration_cast<std::chrono::nanoseconds>(toc-tic).count()<< ;

    for (uint32_t u = 0; u < ueNodes->GetN(); ++u)
    {
        Ptr<MobilityModel> modelu = ueNodes->Get(u)->GetObject<MobilityModel>();
        Ptr<MobilityModel> modelb = gnbNodes->Get(0)->GetObject<MobilityModel>();
        Vector position = modelu->GetPosition ();
        double distance = modelu->GetDistanceFrom (modelb);
        *os  << now.GetSeconds()<< "\t" << (u+1) << "\t"<< position.x << "\t" << position.y << "\t" << distance << std::endl;


    }
    tic=toc;


    
    Simulator::Schedule(MilliSeconds(100), &CalculatePosition, ueNodes, gnbNodes, os);
}

/**
 * Adds Normal Distributed Noise to the specified Physical layer (it is assumed that corresponds to the UE)
 * The function is implemented to be called at the same time as `DlDataSinrCallback`, this implies that unused arguments 
 * had to be added so it would function.
 * 
 * \example  Config::ConnectWithoutContext("/NodeList/.../DeviceList/.../ComponentCarrierMapUe/.../NrUePhy/DlDataSinr",
 *                  MakeBoundCallback(&AddRandomNoise, uePhy))
 * 
*/
static void AddRandomNoise(Ptr<NrPhy> ue_phy)
{
    Ptr<NormalRandomVariable> awgn = CreateObject<NormalRandomVariable>();
    awgn->SetAttribute("Mean", DoubleValue(NOISE_MEAN));
    awgn->SetAttribute("Variance", DoubleValue(NOISE_VAR));
    awgn->SetAttribute("Bound", DoubleValue(NOISE_BOUND));

    ue_phy->SetNoiseFigure(awgn->GetValue());

    /*
    Simulator::Schedule(MilliSeconds(1000),
                        &NrPhy::SetNoiseFigure,
                        ue_phy,
                        awgn->GetValue()); // Default ns3 noise: 5 dB
    */
}

#pragma endregion trace_n_utils_functions
