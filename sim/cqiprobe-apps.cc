#include "ns3/core-module.h"
#include "ns3/applications-module.h"
#include "ns3/internet-module.h"

#include "cmdline-colors.h"
#include "cqiprobe-apps.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("MyAppComp");

class MyAppTag : public Tag
{
public:
  MyAppTag ()
  {
  }

  MyAppTag (Time sendTs) : m_sendTs (sendTs)
  {
  }

  static TypeId GetTypeId (void)
  {
    static TypeId tid = TypeId ("ns3::MyAppTag")
      .SetParent<Tag> ()
      .AddConstructor<MyAppTag> ();
    return tid;
  }

  virtual TypeId  GetInstanceTypeId (void) const
  {
    return GetTypeId ();
  }

  virtual void  Serialize (TagBuffer i) const
  {
    i.WriteU64 (m_sendTs.GetNanoSeconds ());
  }

  virtual void  Deserialize (TagBuffer i)
  {
    m_sendTs = NanoSeconds (i.ReadU64 ());
  }

  virtual uint32_t  GetSerializedSize () const
  {
    return sizeof (m_sendTs);
  }

  virtual void Print (std::ostream &os) const
  {
    std::cout << m_sendTs;
  }

  Time m_sendTs;
};

MyApp::MyApp ()
  : m_socket (0),
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
  m_socket = 0;
}

void
MyApp::Setup (Ptr<Socket> socket, Address address, uint32_t packetSize, uint32_t nPackets, DataRate dataRate)
{
  m_socket = socket;
  m_peer = address;
  m_packetSize = packetSize;
  m_nPackets = nPackets;
  m_dataRate = dataRate;
}

void
MyApp::ChangeDataRate (DataRate rate)
{
  m_dataRate = rate;
}

void
MyApp::StartApplication (void)
{
  m_running = true;
  m_packetsSent = 0;
  m_socket->Bind ();
  m_socket->Connect (m_peer);
  SendPacket ();
}

void
MyApp::StopApplication (void)
{
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
MyApp::SendPacket (void)
{
    Ptr<Packet> packet = Create<Packet> (m_packetSize);
    MyAppTag tag (Simulator::Now ());

    m_socket->Send (packet);
    if (++m_packetsSent < m_nPackets)
    {
        NS_LOG_DEBUG("Sent a packet at " << Simulator::Now().GetSeconds());
        ScheduleTx ();
    }
    else
    {
        std::cout  <<  red << "APP END" << clear << std::endl;

    }
}



void
MyApp::ScheduleTx (void)
{
  if (m_running)
    {
      Time tNext (Seconds (m_packetSize * 8 / static_cast<double> (m_dataRate.GetBitRate ())));
      m_sendEvent = Simulator::Schedule (tNext, &MyApp::SendPacket, this);
    }
    else
    {
        std::cout  <<  red << "APP STOPPED" << clear << std::endl;

    }
}

