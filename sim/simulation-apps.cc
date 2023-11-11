#include "ns3/core-module.h"
#include "ns3/applications-module.h"
#include "ns3/internet-module.h"

#include "cmdline-colors.h"
#include "simulation-apps.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("MyAppComp");

MyApp::MyApp ()
  : m_socket (nullptr),
    m_peer (),
    m_packetSize (0),
    m_nPackets (0),
    m_dataRate (0),
    m_sendEvent (),
    m_running (false),
    m_packetsSent (0)
{
}

MyApp::~MyApp ()
{
  m_socket = nullptr;
}

TypeId
MyApp::GetTypeId()
{
    static TypeId tid =
        TypeId("ns3::MyAppComp")
            .SetParent<Application>()
            .SetGroupName("MyAppComp")
            .AddAttribute("DataRate",
                          "DataRate of the app",
                          DataRateValue(0),
                          MakeDataRateAccessor(&MyApp::m_dataRate),
                          MakeDataRateChecker());
    return tid;
}

void
MyApp::Setup (Ptr<Socket> socket, Address address, uint32_t packetSize, uint32_t nPackets, DataRate dataRate)
{
  NS_LOG_FUNCTION(this << socket << address << packetSize << nPackets << dataRate);
  m_socket = socket;
  m_peer = address;
  m_packetSize = packetSize;
  m_nPackets = nPackets;
  m_dataRate = dataRate;
}

void
MyApp::ChangeDataRate (DataRate rate)
{
  NS_LOG_FUNCTION(this << rate);
  m_dataRate = rate;
}

void
MyApp::StartApplication()
{
  NS_LOG_FUNCTION(this);
  m_running = true;
  m_packetsSent = 0;
  m_socket->Bind ();
  int result = m_socket->Connect (m_peer);
  std::clog << "App Connect Result " << result << std::endl;
  SendPacket ();
}

void
MyApp::StopApplication()
{
  NS_LOG_FUNCTION(this);
  m_running = false;

  if (m_sendEvent.IsRunning ())
    {
    //   std::cout  <<  red << "CANCEL SOCKET" << clear << std::endl;
      Simulator::Cancel (m_sendEvent);
    }

  if (m_socket)
    {
    //   std::cout  <<  red << "CLOSE SOCKET" << clear << std::endl;
      m_socket->Close ();
    }
}

void
MyApp::SendPacket()
{
    NS_LOG_FUNCTION(this);
    Ptr<Packet> packet = Create<Packet>(m_packetSize);
    //MyAppTag tag (Simulator::Now ());
    packet->EnablePrinting();
    // NS_LOG_DEBUG("txBuff before: " << m_socket->GetTxAvailable());
    NS_LOG_DEBUG("Will send a packet at " << Simulator::Now().GetSeconds());
    NS_LOG_DEBUG("Packet sent " << packet->ToString());
    m_socket->Send (packet);
    // NS_LOG_DEBUG("Packet just sent information: ");
    // packet->Print(std::clog);
    // NS_LOG_DEBUG(" ");
    // NS_LOG_DEBUG("txBuff after: " << m_socket->GetTxAvailable());
    if (++m_packetsSent < m_nPackets)
    {
        ScheduleTx ();
    }
    else
    {
        std::cout  <<  TXT_RED << "APP END" << TXT_CLEAR << std::endl;

    }
}

void
MyApp::ScheduleTx()
{
  NS_LOG_FUNCTION(this);
  if (m_running)
    {
      Time tNext (Seconds (m_packetSize * 8 / static_cast<double> (m_dataRate.GetBitRate ())));
      m_sendEvent = Simulator::Schedule (tNext, &MyApp::SendPacket, this);
    }
  else
    {
      std::cout  <<  TXT_RED << "APP STOPPED" << TXT_CLEAR << std::endl;
    }
}

